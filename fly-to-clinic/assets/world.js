/* Klinik Nissa — "Fly to the clinic" 3D world.
 *
 * Everything on screen is a pure function of the composition time t (seconds), so
 * HyperFrames can seek to any frame and get the same picture (no clocks, no Math.random).
 *
 *  - The map (roads, buildings, parks, water, land use) comes from OpenStreetMap through
 *    tools/build_nav_map.py → assets/map-data.js. Metres, x = east, z = south, y = up.
 *  - The route is the OSRM driving route from Plaza Tol Nilai to Jalan BBN 1/3C.
 *  - Two WebGL canvases: #gl (city, pins, arrows, trail) and #gl-fly (the fly mascot and
 *    its air trail), so the fly can stay sharp above the HTML labels and end card.
 */
(function () {
  "use strict";
  const M = window.MAP;
  const W = 1080, H = 1920;

  // ------------------------------------------------------------------ small maths
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, u) => a + (b - a) * u;
  const smooth = (u) => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };
  const smoother = (u) => { u = clamp(u, 0, 1); return u * u * u * (u * (u * 6 - 15) + 10); };
  const win = (t, a, b, fi = 0.25, fo = 0.25) => smooth((t - a) / fi) * (1 - smooth((t - (b - fo)) / fo));
  const backOut = (u, s = 1.9) => { u = clamp(u, 0, 1) - 1; return 1 + (s + 1) * u * u * u + s * u * u; };
  const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  function rng(seed) { // mulberry32: deterministic scatter for trees
    let a = seed >>> 0;
    return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  // Monotone cubic (Fritsch–Carlson) through keyframes [[t, v], …]: smooth, no overshoot, seekable.
  function pchip(keys) {
    const x = keys.map((k) => k[0]), y = keys.map((k) => k[1]), n = x.length;
    const d = [], m = new Array(n).fill(0);
    for (let i = 0; i < n - 1; i++) d.push((y[i + 1] - y[i]) / (x[i + 1] - x[i]));
    m[0] = d[0]; m[n - 1] = d[n - 2];
    for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (2 * d[i - 1] * d[i]) / (d[i - 1] + d[i]);
    for (let i = 0; i < n - 1; i++) if (d[i] === 0) { m[i] = 0; m[i + 1] = 0; }
    return (t) => {
      if (t <= x[0]) return y[0];
      if (t >= x[n - 1]) return y[n - 1];
      let i = 0; while (t > x[i + 1]) i++;
      const h = x[i + 1] - x[i], u = (t - x[i]) / h, u2 = u * u, u3 = u2 * u;
      return (2 * u3 - 3 * u2 + 1) * y[i] + (u3 - 2 * u2 + u) * h * m[i] + (-2 * u3 + 3 * u2) * y[i + 1] + (u3 - u2) * h * m[i + 1];
    };
  }

  // ------------------------------------------------------------------ route helpers
  const RP = M.route, NS = RP.length / 2, STEP = M.step, LEN = M.length;
  const TX = new Float64Array(NS), TZ = new Float64Array(NS), PX = new Float64Array(NS + 1), PZ = new Float64Array(NS + 1);
  for (let i = 0; i < NS; i++) {
    const j = Math.min(NS - 1, i + 1), k = j === i ? i - 1 : i;
    const dx = RP[2 * j] - RP[2 * k], dz = RP[2 * j + 1] - RP[2 * k + 1], l = Math.hypot(dx, dz) || 1;
    TX[i] = dx / l; TZ[i] = dz / l; PX[i + 1] = PX[i] + TX[i]; PZ[i + 1] = PZ[i] + TZ[i];
  }
  function routeAt(s) {
    const f = clamp(s, 0, LEN) / STEP; const i = Math.min(NS - 2, Math.floor(f)); const u = clamp(f - i, 0, 1);
    return new THREE.Vector3(lerp(RP[2 * i], RP[2 * i + 2], u), 0, lerp(RP[2 * i + 1], RP[2 * i + 3], u));
  }
  // Average direction of the road over [s-back, s+ahead]; the window is what smooths the camera.
  function dirAt(s, back, ahead) {
    const i0 = clamp(Math.floor((s - back) / STEP), 0, NS - 1), i1 = clamp(Math.ceil((s + ahead) / STEP), i0 + 1, NS);
    const x = PX[i1] - PX[i0], z = PZ[i1] - PZ[i0], l = Math.hypot(x, z) || 1;
    return new THREE.Vector3(x / l, 0, z / l);
  }
  const yawOf = (v) => Math.atan2(v.x, v.z);
  const angDiff = (a, b) => { let d = a - b; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; return d; };

  const LM = M.landmarks;
  const stepS = (name) => M.steps.find((s) => s.name === name).s;
  const S_LIGHT = M.lights[0];            // first traffic light (NL01) — turn right
  const S_LEFT1 = stepS("Jalan BBN 1/3"); // left at the KFC corner
  const S_LEFT2 = M.steps.filter((s) => s.mod === "left")[1].s; // left into Putra Point
  const S_END = LEN;

  // ================================================================== choreography (seconds)
  // Distance along the route (metres) as a function of time. Plateaus = the fly hovers.
  const S = pchip([
    [1.3, 0], [1.95, 110], [2.6, 1450], [2.88, S_LIGHT - 4], [3.12, S_LIGHT], [3.6, S_LIGHT + 150],
    [4.45, LM.mcd.s], [5.05, S_LEFT1 - 50], [5.4, S_LEFT1], [5.85, S_LEFT1 + 55],
    [6.55, LM.dataran.s], [7.45, 3150], [8.9, S_LEFT2 - 20], [9.45, S_LEFT2 + 12], [10.25, S_END - 30], [10.62, S_END], [15, S_END],
  ]);
  // Camera distance from its look-at point (m) and pitch below horizontal (deg).
  const CAMD = pchip([
    [1.3, 520], [1.95, 470], [2.55, 600], [2.95, 300], [3.25, 300], [3.7, 480], [4.6, 420], [5.3, 290], [5.9, 300],
    [7.4, 285], [8.9, 300], [9.5, 250], [10.4, 205], [11.2, 200], [11.6, 230], [15, 330],
  ]);
  const PITCH = pchip([
    [1.3, 50], [2.55, 46], [2.95, 52], [3.7, 47], [5.3, 52], [7.4, 47], [9.5, 52], [10.4, 60], [11.2, 62], [15, 66],
  ]);
  const T_DIVE0 = 0.95, T_DIVE1 = 1.75; // overview → chase rig blend

  // ================================================================== renderers
  function makeRenderer(canvas, alpha) {
    const r = new THREE.WebGLRenderer({ canvas, antialias: true, alpha, preserveDrawingBuffer: true, powerPreference: "high-performance" });
    r.setPixelRatio(1);
    r.setSize(W, H, false);
    r.outputColorSpace = THREE.SRGBColorSpace;
    r.toneMapping = THREE.ACESFilmicToneMapping;
    r.toneMappingExposure = 1.05;
    return r;
  }
  const renderer = makeRenderer(document.getElementById("gl"), false);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const flyRenderer = makeRenderer(document.getElementById("gl-fly"), true);
  flyRenderer.setClearColor(0x000000, 0);

  // Studio environment for glossy reflections (built in code, no HDR file).
  function studioEnv(r) {
    const env = new THREE.Scene();
    const room = new THREE.Mesh(new THREE.BoxGeometry(20, 12, 20), new THREE.MeshBasicMaterial({ color: 0x1a3358, side: THREE.BackSide }));
    env.add(room);
    const panel = (c, i, x, y, z, sx, sy, sz) => {
      const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), new THREE.MeshBasicMaterial({ color: new THREE.Color(c).multiplyScalar(i) }));
      m.position.set(x, y, z); env.add(m);
    };
    panel(0xffffff, 6, 0, 5.8, 0, 10, 0.2, 6);      // soft box above
    panel(0xfff1d6, 4, -9.8, 2, 0, 0.2, 5, 8);      // warm key
    panel(0x26d6d2, 3, 9.8, 1, -3, 0.2, 4, 6);      // turquoise rim
    panel(0xffe100, 1.5, 0, 0, 9.8, 6, 2, 0.2);     // golden bounce
    const pm = new THREE.PMREMGenerator(r);
    const tex = pm.fromScene(env, 0.035).texture;
    pm.dispose();
    return tex;
  }

  // ================================================================== city scene
  const scene = new THREE.Scene();
  const NAVY = new THREE.Color(0x102849);
  {
    const c = document.createElement("canvas"); c.width = 4; c.height = 256;
    const g = c.getContext("2d"), gr = g.createLinearGradient(0, 0, 0, 256);
    gr.addColorStop(0, "#071733"); gr.addColorStop(0.55, "#123a6b"); gr.addColorStop(1, "#2d8fa6");
    g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
    scene.background = tex;
  }
  scene.fog = new THREE.Fog(0x16406f, 600, 3000);
  scene.environment = studioEnv(renderer); // glossy pins/arrows; matte city materials opt out below

  const camera = new THREE.PerspectiveCamera(42, W / H, 1, 20000);
  const hemi = new THREE.HemisphereLight(0xcfeeff, 0x0d2547, 1.15);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xfff0d8, 2.6);
  const SUN_DIR = new THREE.Vector3(-0.55, 1.0, -0.25).normalize();
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.6;
  scene.add(sun, sun.target);

  const flatMat = (hex, extra = {}) => new THREE.MeshStandardMaterial({ color: hex, roughness: 0.92, metalness: 0, envMapIntensity: 0, side: THREE.DoubleSide, ...extra });
  // Flat ground layers are drawn bottom-up without writing depth (no z-fighting at any zoom).
  function flatLayer(geom, mat, order) {
    mat.depthWrite = false;
    const m = new THREE.Mesh(geom, mat);
    m.renderOrder = order; m.receiveShadow = true;
    scene.add(m);
    return m;
  }

  // Ground
  const [WX0, WZ0, WX1, WZ1] = M.window;
  {
    const g = new THREE.PlaneGeometry(16000, 16000); g.rotateX(-Math.PI / 2);
    const m = new THREE.Mesh(g, flatMat(0x173a66));
    m.renderOrder = -20; m.receiveShadow = true; scene.add(m);
  }

  // --- polygons (land use, parks, water) → one geometry per kind
  const poly2shape = (p) => { const s = new THREE.Shape(); for (let i = 0; i < p.length; i += 2) (i ? s.lineTo(p[i], -p[i + 1]) : s.moveTo(p[i], -p[i + 1])); return s; };
  function mergeGeoms(list) { // non-indexed merge of position/normal (+ optional color)
    list = list.map((g) => (g.index ? g.toNonIndexed() : g));
    let n = 0; list.forEach((g) => (n += g.attributes.position.count));
    const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), hasCol = list.every((g) => g.attributes.color);
    const col = hasCol ? new Float32Array(n * 3) : null;
    let o = 0;
    for (const g of list) {
      pos.set(g.attributes.position.array, o * 3); nor.set(g.attributes.normal.array, o * 3);
      if (col) col.set(g.attributes.color.array, o * 3);
      o += g.attributes.position.count;
    }
    const out = new THREE.BufferGeometry();
    out.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    out.setAttribute("normal", new THREE.BufferAttribute(nor, 3));
    if (col) out.setAttribute("color", new THREE.BufferAttribute(col, 3));
    return out;
  }
  const AREA_STYLE = {
    urban: [0x1e4776, -18, 0.05], parking: [0x2a5282, -16, 0.1], green: [0x23806f, -15, 0.15],
    water: [0x2a74c4, -14, 0.12], plaza: [0x8fc6cf, -13, 0.25],
  };
  const areasByKind = {};
  for (const a of M.areas) (areasByKind[a.k] = areasByKind[a.k] || []).push(a);
  const plazaArea = areasByKind.plaza && areasByKind.plaza[0];
  for (const k in areasByKind) {
    const [hex, order, y] = AREA_STYLE[k];
    const gs = areasByKind[k].map((a) => { const g = new THREE.ShapeGeometry(poly2shape(a.p)); g.rotateX(-Math.PI / 2); g.translate(0, y, 0); return g; });
    const mat = k === "water" ? flatMat(hex, { roughness: 0.25, metalness: 0.2 }) : flatMat(hex);
    flatLayer(mergeGeoms(gs), mat, order);
  }

  // --- roads → ribbons with round joins
  function ribbonArrays(p, w, y, out) {
    const n = p.length / 2; if (n < 2) return;
    const hw = w / 2;
    let prevL = null, prevR = null;
    for (let i = 0; i < n; i++) {
      const a = Math.max(0, i - 1), b = Math.min(n - 1, i + 1);
      let tx = p[2 * b] - p[2 * a], tz = p[2 * b + 1] - p[2 * a + 1]; const l = Math.hypot(tx, tz) || 1; tx /= l; tz /= l;
      let s = 1;
      if (i > 0 && i < n - 1) { // miter length, capped
        const sx = p[2 * i] - p[2 * i - 2], sz = p[2 * i + 1] - p[2 * i - 1], sl = Math.hypot(sx, sz) || 1;
        s = 1 / Math.max(0.5, Math.abs((sx / sl) * tx + (sz / sl) * tz));
      }
      const nx = -tz * hw * s, nz = tx * hw * s;
      const L = [p[2 * i] + nx, y, p[2 * i + 1] + nz], R = [p[2 * i] - nx, y, p[2 * i + 1] - nz];
      if (prevL) out.push(...prevL, ...R, ...prevR, ...prevL, ...L, ...R);
      prevL = L; prevR = R;
    }
  }
  function discArrays(x, z, r, y, out, seg = 10) {
    for (let k = 0; k < seg; k++) {
      const a0 = (k / seg) * Math.PI * 2, a1 = ((k + 1) / seg) * Math.PI * 2;
      out.push(x, y, z, x + Math.cos(a1) * r, y, z + Math.sin(a1) * r, x + Math.cos(a0) * r, y, z + Math.sin(a0) * r);
    }
  }
  function flatGeom(arr) {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(arr, 3));
    const nor = new Float32Array(arr.length); for (let i = 1; i < arr.length; i += 3) nor[i] = 1;
    g.setAttribute("normal", new THREE.BufferAttribute(nor, 3));
    return g;
  }
  const roadSets = { curb: [], minor: [], link: [], major: [], mark: [] };
  for (const r of M.roads) {
    const p = r.p, n = p.length / 2;
    const set = roadSets[r.c];
    ribbonArrays(p, r.w, 0, set);
    discArrays(p[0], p[1], r.w / 2, 0, set); discArrays(p[2 * n - 2], p[2 * n - 1], r.w / 2, 0, set);
    if (r.c === "major") {
      ribbonArrays(p, r.w + 3, 0, roadSets.curb);
      // dashed centre line: 6 m dashes every 14 m
      let acc = 0;
      for (let i = 1; i < n; i++) {
        const x0 = p[2 * i - 2], z0 = p[2 * i - 1], x1 = p[2 * i], z1 = p[2 * i + 1], l = Math.hypot(x1 - x0, z1 - z0);
        for (let d = (14 - (acc % 14)) % 14; d < l; d += 14) {
          const u0 = d / l, u1 = Math.min(1, (d + 6) / l);
          ribbonArrays([lerp(x0, x1, u0), lerp(z0, z1, u0), lerp(x0, x1, u1), lerp(z0, z1, u1)], 0.7, 0, roadSets.mark);
        }
        acc += l;
      }
    }
  }
  const ROAD_STYLE = { curb: [0x9cc0dd, -12, 0.3], minor: [0x2f5584, -11, 0.4], link: [0x3c6699, -10, 0.45], major: [0x45709f, -9, 0.5], mark: [0xf4f8ff, -8, 0.6] };
  for (const k in roadSets) {
    const [hex, order, y] = ROAD_STYLE[k];
    const g = flatGeom(roadSets[k]); g.translate(0, y, 0);
    flatLayer(g, flatMat(hex, k === "mark" ? { emissive: 0x6c8fb3, emissiveIntensity: 0.3 } : {}), order);
  }

  // --- buildings → extruded footprints, vertex-coloured roofs and walls
  const HSCALE = 1.3;
  const TAG_COLORS = {
    "": [new THREE.Color(0xeaf3fb), new THREE.Color(0xc6dcef)],
    aeon: [new THREE.Color(0xf6f2fa), new THREE.Color(0xb21e86)],  // white mall, magenta roof band
    mcd: [new THREE.Color(0xd52b1e), new THREE.Color(0xffc72c)],   // red walls, golden roof
    kfc: [new THREE.Color(0xf4f4f4), new THREE.Color(0xc8102e)],
  };
  const bGeoms = [];
  const landmarkBoxes = {};
  function addBuilding(pts, h, tag, seed) {
    const g = new THREE.ExtrudeGeometry(poly2shape(pts), { depth: h, bevelEnabled: false });
    g.rotateX(-Math.PI / 2);
    const ng = g.index ? g.toNonIndexed() : g;
    const nor = ng.attributes.normal.array, cnt = ng.attributes.position.count, col = new Float32Array(cnt * 3);
    const [wall, roof] = TAG_COLORS[tag];
    const shade = tag ? 1 : 0.94 + 0.08 * hash(seed);
    for (let i = 0; i < cnt; i++) {
      const c = nor[i * 3 + 1] > 0.5 ? roof : wall;
      col[i * 3] = c.r * shade; col[i * 3 + 1] = c.g * shade; col[i * 3 + 2] = c.b * shade;
    }
    ng.setAttribute("color", new THREE.BufferAttribute(col, 3));
    bGeoms.push(ng);
    if (tag) {
      let x = 0, z = 0; for (let i = 0; i < pts.length; i += 2) { x += pts[i]; z += pts[i + 1]; }
      landmarkBoxes[tag] = { x: x / (pts.length / 2), z: z / (pts.length / 2), h };
    }
  }
  M.buildings.forEach((b, i) => addBuilding(b.p, Math.max(4, b.h * HSCALE), b.t, i));
  // KFC Nilai Square is mapped as a point only: model a small restaurant block on that exact point.
  {
    const k = LM.kfc, hw = 9, hd = 7;
    addBuilding([k.x - hw, k.z - hd, k.x + hw, k.z - hd, k.x + hw, k.z + hd, k.x - hw, k.z + hd], 9, "kfc", 999);
  }
  const buildings = new THREE.Mesh(mergeGeoms(bGeoms), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.6, metalness: 0.05, envMapIntensity: 0.2 }));
  buildings.castShadow = true; buildings.receiveShadow = true;
  scene.add(buildings);

  // --- trees (stylised, deterministic scatter): parks, road verges and empty land
  const roadGrid = new Map(); // 40 m grid of road segments, used to keep trees off the asphalt
  const cellKey = (x, z) => `${Math.floor(x / 40)},${Math.floor(z / 40)}`;
  for (const r of M.roads) {
    const p = r.p;
    for (let i = 2; i < p.length; i += 2) {
      const seg = [p[i - 2], p[i - 1], p[i], p[i + 1], r.w / 2];
      const n = Math.ceil(Math.hypot(p[i] - p[i - 2], p[i + 1] - p[i - 1]) / 20) + 1;
      for (let k = 0; k <= n; k++) {
        const key = cellKey(lerp(p[i - 2], p[i], k / n), lerp(p[i - 1], p[i + 1], k / n));
        if (!roadGrid.has(key)) roadGrid.set(key, new Set());
        roadGrid.get(key).add(seg);
      }
    }
  }
  function nearRoad(x, z, pad) {
    for (let dx = -1; dx <= 1; dx++) for (let dz = -1; dz <= 1; dz++) {
      const set = roadGrid.get(cellKey(x + dx * 40, z + dz * 40)); if (!set) continue;
      for (const [x0, z0, x1, z1, hw] of set) {
        const vx = x1 - x0, vz = z1 - z0, l2 = vx * vx + vz * vz || 1;
        const u = clamp(((x - x0) * vx + (z - z0) * vz) / l2, 0, 1);
        if (Math.hypot(x - (x0 + u * vx), z - (z0 + u * vz)) < hw + pad) return true;
      }
    }
    return false;
  }
  const inPoly = (x, z, p) => { let c = false; for (let i = 0, j = p.length - 2; i < p.length; j = i, i += 2) { const xi = p[i], zi = p[i + 1], xj = p[j], zj = p[j + 1]; if (zi > z !== zj > z && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) c = !c; } return c; };
  const bboxes = M.buildings.map((b) => { let x0 = 1e9, z0 = 1e9, x1 = -1e9, z1 = -1e9; for (let i = 0; i < b.p.length; i += 2) { x0 = Math.min(x0, b.p[i]); x1 = Math.max(x1, b.p[i]); z0 = Math.min(z0, b.p[i + 1]); z1 = Math.max(z1, b.p[i + 1]); } return [x0 - 4, z0 - 4, x1 + 4, z1 + 4]; });
  const inBuilding = (x, z) => bboxes.some((b) => x > b[0] && x < b[2] && z > b[1] && z < b[3]);
  const urbanPolys = (areasByKind.urban || []).concat(areasByKind.parking || []).map((a) => a.p);
  const greenPolys = (areasByKind.green || []).map((a) => a.p);
  const waterPolys = (areasByKind.water || []).map((a) => a.p);
  const trees = [];
  const R = rng(20251027);
  for (let x = WX0; x < WX1; x += 26) for (let z = WZ0; z < WZ1; z += 26) {
    const px = x + (R() - 0.5) * 22, pz = z + (R() - 0.5) * 22, roll = R();
    if (waterPolys.some((p) => inPoly(px, pz, p))) continue;
    const green = greenPolys.some((p) => inPoly(px, pz, p));
    const urban = !green && urbanPolys.some((p) => inPoly(px, pz, p));
    const keep = green ? roll < 0.85 : urban ? roll < 0.12 : roll < 0.4;
    if (!keep || nearRoad(px, pz, 4) || inBuilding(px, pz)) continue;
    trees.push([px, pz, 0.75 + R() * 0.6, R()]);
  }
  if (plazaArea) { // a ring of trees around Dataran Nilai's lawn
    const p = plazaArea.p;
    for (let i = 0; i < p.length; i += 2) trees.push([p[i] * 0.92 + 0.08 * LM.dataran.x, p[i + 1] * 0.92 + 0.08 * LM.dataran.z, 0.9, hash(i)]);
  }
  {
    const crown = new THREE.IcosahedronGeometry(5.5, 1); crown.translate(0, 9, 0);
    const trunk = new THREE.CylinderGeometry(0.7, 0.9, 5, 6); trunk.translate(0, 2.5, 0);
    const tc = (g, c) => { const n = g.index ? g.toNonIndexed() : g; const a = new Float32Array(n.attributes.position.count * 3); for (let i = 0; i < a.length; i += 3) { a[i] = c.r; a[i + 1] = c.g; a[i + 2] = c.b; } n.setAttribute("color", new THREE.BufferAttribute(a, 3)); return n; };
    const tg = mergeGeoms([tc(crown, new THREE.Color(0x3fbf8f)), tc(trunk, new THREE.Color(0x6b4e3a))]);
    const im = new THREE.InstancedMesh(tg, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.8, flatShading: true, envMapIntensity: 0 }), trees.length);
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(), ps = new THREE.Vector3(), tint = new THREE.Color();
    trees.forEach(([x, z, s, v], i) => {
      q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), v * 6.28); sc.set(s, s * (0.9 + v * 0.3), s); ps.set(x, 0, z);
      m4.compose(ps, q, sc); im.setMatrixAt(i, m4);
      im.setColorAt(i, tint.setHSL(0.42 + v * 0.06, 0.55, 0.42 + v * 0.12));
    });
    im.castShadow = true; im.receiveShadow = true;
    scene.add(im);
  }

  // --- route: faint full path ahead + glowing trail behind the fly
  function routeRibbon(width, y) {
    const pos = [], idx = [];
    for (let i = 0; i < NS; i++) {
      const x = RP[2 * i], z = RP[2 * i + 1], nx = -TZ[i] * width / 2, nz = TX[i] * width / 2;
      pos.push(x + nx, y, z + nz, x - nx, y, z - nz);
      if (i) { const a = 2 * i - 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx);
    return g;
  }
  const aheadMat = new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, color: 0xdffcff, transparent: true, opacity: 0.55, depthWrite: false, fog: false });
  const ahead = new THREE.Mesh(routeRibbon(5, 0.8), aheadMat); ahead.renderOrder = -6; scene.add(ahead);
  const glowMat = new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, color: 0x26d6d2, transparent: true, opacity: 0.45, blending: THREE.AdditiveBlending, depthWrite: false, fog: false });
  const glow = new THREE.Mesh(routeRibbon(26, 0.9), glowMat); glow.renderOrder = 5; scene.add(glow);
  const coreMat = new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, color: 0x5ff3ee, transparent: true, opacity: 1, depthWrite: false, fog: false });
  const core = new THREE.Mesh(routeRibbon(9, 1.0), coreMat); core.renderOrder = 6; scene.add(core);
  const hotMat = new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, color: 0xffffff, transparent: true, opacity: 0.9, depthWrite: false, fog: false });
  const hot = new THREE.Mesh(routeRibbon(3, 1.1), hotMat); hot.renderOrder = 7; scene.add(hot);
  const setTrail = (s) => {
    const k = Math.round(clamp(s, 0, LEN) / STEP) * 6;
    core.geometry.setDrawRange(0, k); glow.geometry.setDrawRange(0, k); hot.geometry.setDrawRange(0, k);
    ahead.geometry.setDrawRange(k, NS * 6);
  };

  // --- shared sprite textures
  function radialTex(stops) {
    const c = document.createElement("canvas"); c.width = c.height = 128;
    const g = c.getContext("2d"), gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    stops.forEach(([o, col]) => gr.addColorStop(o, col)); g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  }
  const TEX_GLOW = radialTex([[0, "rgba(255,255,255,1)"], [0.25, "rgba(150,255,250,0.8)"], [1, "rgba(38,214,210,0)"]]);
  const TEX_SHADOW = radialTex([[0, "rgba(4,14,32,0.65)"], [0.6, "rgba(4,14,32,0.25)"], [1, "rgba(4,14,32,0)"]]);

  // --- trail sparkles (deterministic particles that settle onto the road behind the fly)
  const NSPARK = 70;
  const sparkGeo = new THREE.BufferGeometry();
  sparkGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(NSPARK * 3), 3));
  sparkGeo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(NSPARK * 3), 3));
  const sparkMat = new THREE.PointsMaterial({ size: 14, map: TEX_GLOW, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: false, fog: false });
  const sparks = new THREE.Points(sparkGeo, sparkMat); sparks.renderOrder = 8; sparks.frustumCulled = false; scene.add(sparks);

  // --- fly blob shadow on the ground
  const blob = new THREE.Mesh(new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: TEX_SHADOW, transparent: true, depthWrite: false, fog: false }));
  blob.renderOrder = 4; scene.add(blob);

  // --- map pins (holographic): teardrop head, glossy, light beam and pulsing ground ring
  function pinGeometry() {
    // lathe profile: tip at y=0, cone tangent to a round head (r=1) centred at y=2.2
    const pts = [new THREE.Vector2(0, 0)], a0 = -Math.asin(1 / 2.2);
    for (let i = 0; i <= 24; i++) {
      const ang = lerp(a0, Math.PI / 2, i / 24);
      pts.push(new THREE.Vector2(Math.max(0.0001, Math.cos(ang)), 2.2 + Math.sin(ang)));
    }
    return new THREE.LatheGeometry(pts, 40);
  }
  const PIN_GEO = pinGeometry();
  function makePin(hex, ringHex) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(PIN_GEO, new THREE.MeshPhysicalMaterial({ color: hex, roughness: 0.18, metalness: 0.1, clearcoat: 1, clearcoatRoughness: 0.1, emissive: hex, emissiveIntensity: 0.18 }));
    body.castShadow = true;
    const dot = new THREE.Mesh(new THREE.SphereGeometry(0.42, 24, 16), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 0.4 }));
    dot.position.set(0, 2.2, 0.9); dot.scale.set(1, 1, 0.35);
    const band = new THREE.Mesh(new THREE.TorusGeometry(0.52, 0.07, 12, 48), new THREE.MeshStandardMaterial({ color: ringHex, metalness: 1, roughness: 0.25, emissive: ringHex, emissiveIntensity: 0.3 }));
    band.position.set(0, 2.2, 0.88);
    const head = new THREE.Group(); head.add(body, dot, band);
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.9, 1, 24, 1, true), new THREE.MeshBasicMaterial({ color: hex, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false }));
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.75, 1, 48).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: hex, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
    const ring2 = ring.clone(); ring2.material = ring.material.clone();
    g.add(head, beam, ring, ring2);
    scene.add(g);
    return { g, head, beam, ring, ring2, dot };
  }
  // Pose a pin: ground point p, screen-constant size k (fraction of camera distance), pop-in u (0..1).
  function posePin(pin, p, size, u, t, hover) {
    const show = u > 0.001; pin.g.visible = show; if (!show) return;
    const pop = backOut(u, 2.2);
    pin.head.scale.setScalar(size * pop);
    const bob = Math.sin(t * 3.1 + p.x) * 0.25 * size;
    pin.head.position.set(p.x, hover * size + bob, p.z);
    const elev = Math.atan2(camera.position.y - pin.head.position.y, Math.hypot(camera.position.x - p.x, camera.position.z - p.z));
    pin.head.rotation.set(-elev * 0.6, Math.atan2(camera.position.x - p.x, camera.position.z - p.z), 0, "YXZ"); // face the camera
    pin.beam.position.set(p.x, (hover * size) / 2, p.z); pin.beam.scale.set(size * 0.9 * pop, Math.max(0.01, hover * size), size * 0.9 * pop);
    pin.beam.material.opacity = 0.3 * u;
    const ph = (t * 0.9) % 1, ph2 = (t * 0.9 + 0.5) % 1;
    pin.ring.position.set(p.x, 1.2, p.z); pin.ring.scale.setScalar(size * (1 + ph * 3.5) * u); pin.ring.material.opacity = 0.9 * (1 - ph) * u;
    pin.ring2.position.set(p.x, 1.2, p.z); pin.ring2.scale.setScalar(size * (1 + ph2 * 3.5) * u); pin.ring2.material.opacity = 0.9 * (1 - ph2) * u;
  }
  const pins = {
    toll: makePin(0xffe100, 0xffffff), mcd: makePin(0xffe100, 0xffffff), kfc: makePin(0xffe100, 0xffffff),
    dataran: makePin(0xffe100, 0xffffff), aeon: makePin(0xffe100, 0xffffff), dest: makePin(0x26d6d2, 0xffd34d),
  };
  const P_DEST = new THREE.Vector3(LM.clinic.x, 0, LM.clinic.z);
  // Pin a big footprint on its side facing the road: the vertex nearest the route, pulled 30% towards the centre.
  function frontage(poly, sRoad) {
    const r = routeAt(sRoad); let best = 0, bd = Infinity, cx = 0, cz = 0;
    for (let i = 0; i < poly.length; i += 2) { cx += poly[i]; cz += poly[i + 1]; const d = Math.hypot(poly[i] - r.x, poly[i + 1] - r.z); if (d < bd) { bd = d; best = i; } }
    cx /= poly.length / 2; cz /= poly.length / 2;
    return new THREE.Vector3(lerp(poly[best], cx, 0.3), 0, lerp(poly[best + 1], cz, 0.3));
  }
  const pinPos = {
    toll: new THREE.Vector3(LM.toll.x, 0, LM.toll.z),
    mcd: new THREE.Vector3(landmarkBoxes.mcd.x, 0, landmarkBoxes.mcd.z),
    kfc: new THREE.Vector3(LM.kfc.x, 0, LM.kfc.z),
    dataran: plazaArea ? frontage(plazaArea.p, LM.dataran.s) : new THREE.Vector3(LM.dataran.x, 0, LM.dataran.z),
    aeon: frontage(M.buildings.find((b) => b.t === "aeon").p, LM.aeon.s - 120),
  };

  // --- toll plaza canopy (Plaza Tol Nilai), across the carriageway at the OSM toll point
  {
    const g = new THREE.Group();
    const white = new THREE.MeshStandardMaterial({ color: 0xf5f9ff, roughness: 0.4 });
    const canopy = new THREE.Mesh(new THREE.BoxGeometry(70, 2.2, 16), white); canopy.position.y = 10;
    const edge = new THREE.Mesh(new THREE.BoxGeometry(71, 0.8, 16.6), new THREE.MeshStandardMaterial({ color: 0x26d6d2, emissive: 0x26d6d2, emissiveIntensity: 0.9 })); edge.position.y = 8.6;
    g.add(canopy, edge);
    for (let i = -3; i <= 3; i++) {
      const pillar = new THREE.Mesh(new THREE.BoxGeometry(1.6, 9, 1.6), white); pillar.position.set(i * 10.5, 4.5, 0);
      const booth = new THREE.Mesh(new THREE.BoxGeometry(2.6, 3.4, 5), new THREE.MeshStandardMaterial({ color: 0xffe100, roughness: 0.5 })); booth.position.set(i * 10.5, 1.7, 0);
      g.add(pillar, booth);
    }
    g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    const d = dirAt(4, 0, 30);
    g.position.copy(pinPos.toll); g.rotation.y = yawOf(d);
    scene.add(g);
  }

  // --- traffic lights on the route (signal heads face oncoming traffic, green lit)
  const lightModels = M.lights.map((s) => {
    const g = new THREE.Group();
    const dark = new THREE.MeshStandardMaterial({ color: 0x1c2a3d, roughness: 0.5, metalness: 0.4 });
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.55, 14, 12), dark); pole.position.y = 7;
    const arm = new THREE.Mesh(new THREE.BoxGeometry(10, 0.6, 0.6), dark); arm.position.set(5, 13.4, 0);
    const box = new THREE.Mesh(new THREE.BoxGeometry(2.2, 6.4, 1.6), dark); box.position.set(9, 11, 0);
    g.add(pole, arm, box);
    const lamps = [[0xff3b3b, 13], [0xffb400, 11], [0x2bff88, 9]].map(([c, y]) => {
      const l = new THREE.Mesh(new THREE.SphereGeometry(0.75, 16, 12), new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 0.15 }));
      l.position.set(9, y, 0.85); g.add(l); return l;
    });
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: TEX_GLOW, color: 0x2bff88, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
    halo.position.set(9, 9, 1.2); halo.scale.setScalar(9); g.add(halo);
    g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
    const p = routeAt(s), d = dirAt(s, 25, 0), right = new THREE.Vector3(-d.z, 0, d.x);
    g.position.copy(p).addScaledVector(d, -14).addScaledVector(right, -13); // near-side (left) kerb, before the stop line
    g.rotation.y = yawOf(d) + Math.PI;
    g.scale.setScalar(2.6);
    scene.add(g);
    return { g, lamps, halo, s };
  });

  // --- 3D turn arrows that follow the real turn geometry and rise out of the road
  function turnArrow(sTurn, back, ahead) {
    const left = [], right = [], w = 6;
    for (let s = sTurn - back; s <= sTurn + ahead; s += 3) {
      const p = routeAt(s), d = dirAt(s, 6, 6);
      left.push([p.x - d.z * w, p.z + d.x * w]); right.push([p.x + d.z * w, p.z - d.x * w]);
    }
    const tip = routeAt(sTurn + ahead), d = dirAt(sTurn + ahead, 12, 0);
    const head = [[tip.x - d.z * 15, tip.z + d.x * 15], [tip.x + d.x * 22, tip.z + d.z * 22], [tip.x + d.z * 15, tip.z - d.x * 15]];
    const outline = left.concat([head[0], head[1], head[2]]).concat(right.reverse());
    const shape = new THREE.Shape(); outline.forEach(([x, z], i) => (i ? shape.lineTo(x, -z) : shape.moveTo(x, -z)));
    const g = new THREE.ExtrudeGeometry(shape, { depth: 2.4, bevelEnabled: true, bevelSize: 0.8, bevelThickness: 0.8, bevelSegments: 2 });
    g.rotateX(-Math.PI / 2);
    const mat = new THREE.MeshStandardMaterial({ color: 0x0b9f9b, emissive: 0x26d6d2, emissiveIntensity: 0.3, roughness: 0.35, metalness: 0.2, envMapIntensity: 0.4, transparent: true });
    const m = new THREE.Mesh(g, mat); m.castShadow = true; m.renderOrder = 3;
    const glowM = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: 0x9ffcf8, transparent: true, opacity: 0.2, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
    const grp = new THREE.Group(); grp.add(m, glowM); scene.add(grp);
    return { grp, mat, glowM };
  }
  const arrows = [
    { a: turnArrow(S_LIGHT, 55, 70), t0: 2.7, t1: 3.95 },     // right at the first traffic light
    { a: turnArrow(S_LEFT1, 55, 60), t0: 4.75, t1: 5.95 },    // left at the KFC corner
    { a: turnArrow(S_LEFT2, 40, 28), t0: 8.75, t1: 9.85 },    // left into Putra Point
  ];

  // ================================================================== the fly (overlay scene)
  const flyScene = new THREE.Scene();
  flyScene.environment = studioEnv(flyRenderer);
  flyScene.add(new THREE.HemisphereLight(0xe8fbff, 0x16355f, 1.0));
  const flyKey = new THREE.DirectionalLight(0xfff3e0, 2.4); flyScene.add(flyKey, flyKey.target);
  const flyRim = new THREE.DirectionalLight(0x6ff7f2, 2.2); flyScene.add(flyRim, flyRim.target);

  const fly = new THREE.Group();   // world position + heading
  const rig = new THREE.Group();   // bank / pitch / look-back
  fly.add(rig); flyScene.add(fly);
  const turq = new THREE.MeshPhysicalMaterial({ color: 0x26d6d2, metalness: 0.55, roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.08 });
  const turqLight = new THREE.MeshPhysicalMaterial({ color: 0x6ff0ec, metalness: 0.35, roughness: 0.25, clearcoat: 1 });
  const gold = new THREE.MeshStandardMaterial({ color: 0xffc93d, metalness: 1, roughness: 0.28 });
  const navy = new THREE.MeshStandardMaterial({ color: 0x0b1f3d, roughness: 0.2, metalness: 0.2 });
  const white = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.12, clearcoat: 1 });
  const sph = (r, mat, x, y, z, sx = 1, sy = 1, sz = 1) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 40, 28), mat); m.position.set(x, y, z); m.scale.set(sx, sy, sz); rig.add(m); return m; };
  // body: abdomen, thorax, head (local +Z = forward, +Y = up)
  sph(0.62, turq, 0, 0, -0.78, 0.86, 0.78, 1.18);
  [[-0.5, 0.56], [-0.86, 0.5], [-1.18, 0.34]].forEach(([z, r]) => {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r, 0.055, 12, 40), gold); ring.position.set(0, 0, z); ring.scale.set(0.98, 0.9, 1); rig.add(ring);
  });
  sph(0.5, turq, 0, 0.06, 0.08);
  sph(0.5, turqLight, 0, 0.14, 0.72);
  // big friendly eyes
  for (const sx of [-1, 1]) {
    sph(0.36, white, sx * 0.3, 0.38, 0.92);
    sph(0.22, navy, sx * 0.31, 0.38, 1.2, 1, 1.08, 0.45);
    sph(0.075, white, sx * 0.26, 0.47, 1.31);
    sph(0.07, new THREE.MeshStandardMaterial({ color: 0xff8fa3, roughness: 0.6 }), sx * 0.34, 0.06, 1.08, 1, 0.7, 0.5);
  }
  { const smile = new THREE.Mesh(new THREE.TorusGeometry(0.13, 0.028, 8, 20, Math.PI), navy); smile.position.set(0, 0.05, 1.215); smile.rotation.z = Math.PI; rig.add(smile); }
  // antennae
  const antennae = [-1, 1].map((sx) => {
    const g = new THREE.Group(); g.position.set(sx * 0.15, 0.55, 0.86);
    const curve = new THREE.CatmullRomCurve3([new THREE.Vector3(0, 0, 0), new THREE.Vector3(sx * 0.08, 0.3, 0.1), new THREE.Vector3(sx * 0.22, 0.52, 0.32)]);
    g.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 16, 0.03, 8), navy));
    const tip = new THREE.Mesh(new THREE.SphereGeometry(0.085, 20, 14), gold); tip.position.set(sx * 0.22, 0.52, 0.32); g.add(tip);
    rig.add(g); return g;
  });
  // legs (tucked) + two waving arms
  const legMat = navy;
  [[-0.25, -0.15], [0.25, -0.15], [-0.28, -0.45], [0.28, -0.45]].forEach(([x, z]) => {
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.03, 0.42, 8), legMat); leg.position.set(x, -0.42, z); leg.rotation.z = x * 0.9; leg.rotation.x = 0.5; rig.add(leg);
  });
  const arms = [-1, 1].map((sx) => {
    const g = new THREE.Group(); g.position.set(sx * 0.3, -0.12, 0.38);
    const a = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.035, 0.46, 8), legMat); a.position.y = -0.23; g.add(a);
    const hand = new THREE.Mesh(new THREE.SphereGeometry(0.075, 14, 10), gold); hand.position.y = -0.47; g.add(hand);
    g.rotation.z = sx * 0.5; rig.add(g); return g;
  });
  // translucent wings (+ a faint motion-blur ghost each)
  const wingShape = new THREE.Shape();
  wingShape.moveTo(0, 0); wingShape.bezierCurveTo(0.5, 0.42, 1.55, 0.5, 1.92, 0.08); wingShape.bezierCurveTo(2.05, -0.25, 1.1, -0.45, 0, 0);
  const wingGeo = new THREE.ShapeGeometry(wingShape, 24); wingGeo.rotateX(-Math.PI / 2);
  const wingMat = new THREE.MeshPhysicalMaterial({ color: 0xd8fffd, emissive: 0x26d6d2, emissiveIntensity: 0.25, roughness: 0.05, metalness: 0, transparent: true, opacity: 0.42, side: THREE.DoubleSide, iridescence: 1, iridescenceIOR: 1.6, depthWrite: false });
  const ghostMat = wingMat.clone(); ghostMat.opacity = 0.14;
  const edgeGeo = new THREE.BufferGeometry().setFromPoints(wingShape.getPoints(40).map((p) => new THREE.Vector3(p.x, 0, -p.y)));
  const edgeMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85 });
  const wings = [-1, 1].map((sx) => {
    const pivot = new THREE.Group(); pivot.position.set(sx * 0.18, 0.46, 0.0);
    const wing = new THREE.Group(); wing.scale.set(sx, 1, 1); wing.rotation.y = sx * 0.42; // sweep back
    wing.add(new THREE.Mesh(wingGeo, wingMat), new THREE.Line(edgeGeo, edgeMat));
    const ghost = new THREE.Group(); ghost.scale.set(sx, 1, 1); ghost.rotation.y = sx * 0.42; ghost.add(new THREE.Mesh(wingGeo, ghostMat));
    const gPivot = new THREE.Group(); gPivot.position.copy(pivot.position); gPivot.add(ghost);
    pivot.add(wing); rig.add(pivot, gPivot);
    return { pivot, gPivot, sx };
  });
  // soft glow behind the fly
  const flyGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: TEX_GLOW, color: 0x26d6d2, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false }));
  flyGlow.scale.setScalar(4.2); rig.add(flyGlow);

  // air trail behind the fly (camera-facing ribbon through its recent positions)
  const NTR = 28;
  const trailGeo = new THREE.BufferGeometry();
  trailGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(NTR * 2 * 3), 3));
  trailGeo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(NTR * 2 * 4), 4));
  { const idx = []; for (let i = 0; i < NTR - 1; i++) { const a = 2 * i; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); } trailGeo.setIndex(idx); }
  const airTrail = new THREE.Mesh(trailGeo, new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false, side: THREE.DoubleSide }));
  airTrail.frustumCulled = false; flyScene.add(airTrail);

  // The giant hook pin lives in the fly scene so the fly can loop in front of and behind it.
  const bigPin = (() => {
    const g = new THREE.Group();
    const body = new THREE.Mesh(PIN_GEO, new THREE.MeshPhysicalMaterial({ color: 0x26d6d2, roughness: 0.15, metalness: 0.2, clearcoat: 1, emissive: 0x0f8f8c, emissiveIntensity: 0.25 }));
    const band = new THREE.Mesh(new THREE.TorusGeometry(0.54, 0.08, 14, 60), gold); band.position.set(0, 2.2, 0.88);
    const dot = new THREE.Mesh(new THREE.SphereGeometry(0.44, 24, 16), white); dot.position.set(0, 2.2, 0.9); dot.scale.set(1, 1, 0.35);
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: TEX_GLOW, color: 0x26d6d2, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false }));
    halo.position.y = 2.2; halo.scale.setScalar(6);
    g.add(halo, body, band, dot); flyScene.add(g);
    return g;
  })();

  // ================================================================== camera rig
  const UP = new THREE.Vector3(0, 1, 0);
  const OV_TARGET = new THREE.Vector3((LM.toll.x + LM.clinic.x) / 2 + 40, 0, (LM.toll.z + LM.clinic.z) / 2 + 120);
  const OV_DIR = new THREE.Vector3(LM.clinic.x - LM.toll.x, 0, LM.clinic.z - LM.toll.z).normalize();

  // Chase rig: heading is the road direction averaged over a window that grows with height.
  function chase(t) {
    const s = S(t), D = CAMD(t), ph = THREE.MathUtils.degToRad(PITCH(t));
    const wnd = clamp(D * 0.75, 70, 420);
    const h = dirAt(s, wnd * 0.35, wnd);
    const p = routeAt(s);
    const lean = win(t, 5.75, 7.35, 0.5, 0.4) + win(t, 7.45, 9.1, 0.4, 0.4);
    const target = p.clone().addScaledVector(h, D * 0.2).addScaledVector(new THREE.Vector3(-h.z, 0, h.x), D * 0.2 * lean);
    return { s, D, ph, h, target };
  }
  function overview(t) {
    const u = smooth(t / 1.2);
    const D = lerp(2550, 2250, u);
    const target = OV_TARGET.clone();
    const h = OV_DIR.clone().applyAxisAngle(UP, lerp(0.1, 0.0, u));
    return { D, ph: THREE.MathUtils.degToRad(57), h, target };
  }
  function camAt(t) {
    let r;
    if (t <= T_DIVE0) r = overview(t);
    else if (t >= T_DIVE1) r = chase(t);
    else { // swoop: blend overview → chase (log-distance, slerped heading)
      const a = overview(t), b = chase(t), u = smoother((t - T_DIVE0) / (T_DIVE1 - T_DIVE0));
      const ya = yawOf(a.h), yb = ya + angDiff(yawOf(b.h), ya) * u;
      r = { D: Math.exp(lerp(Math.log(a.D), Math.log(b.D), u)), ph: lerp(a.ph, b.ph, u), h: new THREE.Vector3(Math.sin(yb), 0, Math.cos(yb)), target: a.target.clone().lerp(b.target, u), s: b.s };
    }
    if (t > 11.3) { // end: slow rise and orbit around the clinic
      const u = smooth((t - 11.3) / 3.7);
      r.h = r.h.clone().applyAxisAngle(UP, -0.5 * u);
    }
    r.pos = r.target.clone().addScaledVector(r.h, -r.D * Math.cos(r.ph)).add(new THREE.Vector3(0, r.D * Math.sin(r.ph), 0));
    return r;
  }

  // ================================================================== fly pose
  // Map phase: above the route at s(t), banking through turns; hook: screen-choreographed.
  function arrivalOrbit(t, base) {
    const u = smoother((t - 10.35) / 0.9);
    if (u <= 0) return base;
    const c = camAt(t), fwd = c.target.clone().sub(c.pos).setY(0).normalize(), right = new THREE.Vector3(-fwd.z, 0, fwd.x); // screen right
    const size = c.D * 0.034 * 1.08; // destination pin scale on arrival (see frame())
    const centre = P_DEST.clone().setY(size * 5.2);
    const R = size * 2.5;
    const a0 = Math.atan2(-fwd.z, -fwd.x); // start on the camera side of the pin
    const a1 = Math.atan2(-right.z, -right.x) + Math.PI * 2; // end on the screen-left of the pin
    const a = lerp(a0, a1 > a0 ? a1 : a1 + Math.PI * 2, u);
    const orbit = centre.clone().add(new THREE.Vector3(Math.cos(a) * R, Math.sin(u * Math.PI) * size * 1.2, Math.sin(a) * R));
    const vel = new THREE.Vector3(-Math.sin(a), 0, Math.cos(a));
    const k = smooth((t - 10.35) / 0.25);
    return { ...base, pos: base.pos.clone().lerp(orbit, k), yaw: lerp(base.yaw, yawOf(vel), k * (1 - smooth((t - 11.1) / 0.2))), bank: base.bank * (1 - k) + 0.35 * k * (1 - u) };
  }
  function flyOnRoute(t) {
    const r = flyOnRouteRaw(t);
    return t > 10.35 ? arrivalOrbit(t, r) : r;
  }
  function flyOnRouteRaw(t) {
    const c = camAt(t), s = S(t);
    const d = dirAt(s, 10, 16);
    const v = (S(t + 0.02) - S(t - 0.02)) / 0.04;
    const y0 = yawOf(dirAt(s, 18, 0)), y1 = yawOf(dirAt(s, 0, 18));
    const turnRate = (angDiff(y1, y0) / 18) * v; // rad/s
    const p = routeAt(s);
    const alt = c.D * 0.07 + 6;
    return { pos: new THREE.Vector3(p.x, alt, p.z), yaw: yawOf(d), bank: clamp(turnRate * 0.32, -0.75, 0.75), pitch: clamp(v / 2500, 0, 0.35), cam: c, speed: v };
  }
  // World point at NDC (sx, sy) and distance `dist` in front of a camera pose (fov 42°, 9:16).
  const TAN_V = Math.tan(THREE.MathUtils.degToRad(21)), TAN_H = TAN_V * (W / H);
  function camPoint(c, sx, sy, dist) {
    const fwd = c.target.clone().sub(c.pos).normalize();
    const right = new THREE.Vector3().crossVectors(fwd, UP).normalize();
    const up = new THREE.Vector3().crossVectors(right, fwd);
    return c.pos.clone().addScaledVector(fwd, dist).addScaledVector(right, sx * dist * TAN_H).addScaledVector(up, sy * dist * TAN_V);
  }
  const BIG = 140; // giant hook pin scale (m per unit; the pin is 3.2 units tall)
  const LOOP_A0 = -2.2, LOOP_SWEEP = Math.PI * 2.15, LOOP_R = 400;
  let PIN_BASE = null; // world point of the giant pin's tip, chosen on screen from the overview shot
  const pinBase = () => PIN_BASE || (PIN_BASE = camPoint(camAt(0.6), 0.05, -0.35, 1900));
  function bigPinPose(t) {
    const u = backOut(smooth(t / 0.45), 1.6);
    const out = smooth((t - 1.05) / 0.4);
    return { pos: pinBase().clone().add(new THREE.Vector3(0, Math.sin(t * 2.4) * 12 - out * 120, 0)), scale: BIG * u * (1 - out), vis: t < 1.5 };
  }
  // Hook path (pure, no velocity): far by the pin → right up to the lens → loop the pin → dive to the toll.
  function hookPos(t) {
    t = Math.max(0, t);
    const c = camAt(t);
    const pin = pinBase().clone().add(new THREE.Vector3(0, 2.2 * BIG, 0));
    const startP = pin.clone().add(new THREE.Vector3(-260, 300, -200));
    const nearP = camPoint(c, -0.2, -0.3, 300);
    const loopAt = (u) => { const a = LOOP_A0 + LOOP_SWEEP * smoother(u); return pin.clone().add(new THREE.Vector3(Math.cos(a) * LOOP_R, Math.sin(u * Math.PI * 2) * 70 - 40, Math.sin(a) * LOOP_R)); };
    if (t < 0.42) return { pos: startP.lerp(nearP, smoother(t / 0.42)), look: smooth(t / 0.3) };
    if (t < 1.1) { const u = (t - 0.42) / 0.68; return { pos: nearP.lerp(loopAt(u), smooth(u / 0.3)), look: 1 - smooth(u / 0.3) }; }
    const a = loopAt(1), b = flyOnRoute(1.75).pos, u = smoother((t - 1.1) / 0.65);
    const mid = a.clone().lerp(b, 0.5); mid.y += 150;
    return { pos: a.lerp(mid, u).lerp(mid.clone().lerp(b, u), u), look: 0 }; // quadratic Bézier
  }
  function flyAt(t) {
    if (t >= 1.75) return flyOnRoute(t);
    const h = hookPos(t), prev = hookPos(t - 0.03).pos;
    const vel = h.pos.clone().sub(prev);
    if (vel.lengthSq() < 1e-6) vel.set(0, 0, 1);
    return { pos: h.pos, yaw: Math.atan2(vel.x, vel.z), bank: 0, pitch: clamp(-vel.y / (vel.length() + 1e-6), -0.6, 0.6), cam: camAt(t), look: h.look, speed: vel.length() / 0.03 };
  }
  const flyAtPos = (t) => (t >= 1.75 ? flyOnRoute(t).pos : hookPos(t).pos);

  // Screen-size of the fly (as a fraction of camera distance) over time.
  const FLY_SIZE = pchip([[0, 0.012], [0.42, 0.11], [0.62, 0.05], [1.1, 0.04], [1.75, 0.042], [10.6, 0.042], [11.5, 0.045], [12.2, 0.05], [15, 0.05]]);

  // ================================================================== per-frame
  const tmpV = new THREE.Vector3();
  function project(v) {
    tmpV.copy(v).project(camera);
    return { x: (tmpV.x * 0.5 + 0.5) * W, y: (-tmpV.y * 0.5 + 0.5) * H, behind: tmpV.z > 1 };
  }
  const anchors = {}; // screen positions for the HTML layer

  function poseFly(t, f, scaleK) {
    // look-back: turn to face the camera during hovers and on arrival
    const LOOK = Math.max(f.look || 0, win(t, 2.8, 3.25, 0.12, 0.15) * 0.6, win(t, 10.55, 15.5, 0.35, 0.1));
    const camYaw = Math.atan2(camera.position.x - f.pos.x, camera.position.z - f.pos.z);
    const yaw = f.yaw + angDiff(camYaw, f.yaw) * LOOK;
    fly.position.copy(f.pos);
    fly.rotation.set(0, yaw, 0);
    const distCam = camera.position.distanceTo(f.pos);
    fly.scale.setScalar(distCam * scaleK);
    const elev = Math.atan2(camera.position.y - f.pos.y, Math.hypot(camera.position.x - f.pos.x, camera.position.z - f.pos.z));
    rig.rotation.set(f.pitch * (1 - LOOK) - Math.min(elev, 1.1) * 0.8 * LOOK, 0, f.bank * (1 - LOOK));
    rig.position.y = Math.sin(t * 5.3) * 0.12;
    // wings: 7.5 Hz flap → readable 4-frame cycle at 30 fps; faster during the wing-powered burst
    const burst = win(t, 3.45, 3.9, 0.08, 0.2);
    const ph = t * (7.5 + burst * 2.5) * Math.PI * 2;
    for (const w of wings) {
      w.pivot.rotation.z = w.sx * (0.25 + 0.6 * Math.sin(ph));
      w.gPivot.rotation.z = w.sx * (0.25 + 0.6 * Math.sin(ph - 1.6));
    }
    antennae.forEach((a, i) => { a.rotation.x = Math.sin(t * 6 + i) * 0.12 - (f.speed > 200 ? 0.25 : 0); a.rotation.z = Math.sin(t * 4.3 + i * 2) * 0.1; });
    // waving arm on arrival and on the end card; pointing during the hook close-up
    const wave = win(t, 10.75, 15.5, 0.2, 0.1) + win(t, 0.25, 0.6, 0.1, 0.1);
    arms[1].rotation.z = lerp(0.5, 2.4 + Math.sin(t * 9) * 0.45, wave);
    arms[0].rotation.z = -0.5;
    flyGlow.material.opacity = 0.35 + 0.2 * Math.sin(t * 7);
  }

  function updateAirTrail(t, scaleK) {
    const pos = trailGeo.attributes.position.array, col = trailGeo.attributes.color.array;
    const fwdCam = new THREE.Vector3(); camera.getWorldDirection(fwdCam);
    const pts = [];
    // trail spans ~5 body lengths whatever the speed
    const body = camera.position.distanceTo(flyAtPos(t)) * scaleK * 2.4;
    const spd = Math.max(1, flyAtPos(t).distanceTo(flyAtPos(Math.max(0, t - 0.02))) / 0.02);
    const dt = clamp((body * 5) / (spd * NTR), 0.002, 0.011);
    for (let i = 0; i < NTR; i++) pts.push(flyAtPos(Math.max(0, t - i * dt)));
    const width0 = body * 0.2;
    for (let i = 0; i < NTR; i++) {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(NTR - 1, i + 1)];
      const tan = b.clone().sub(a); if (tan.lengthSq() < 1e-6) tan.set(1, 0, 0);
      const side = new THREE.Vector3().crossVectors(tan, fwdCam).normalize().multiplyScalar(width0 * (1 - i / NTR));
      const k = i * 6, c4 = i * 8, fade = Math.pow(1 - i / NTR, 1.3);
      pos[k] = pts[i].x + side.x; pos[k + 1] = pts[i].y + side.y; pos[k + 2] = pts[i].z + side.z;
      pos[k + 3] = pts[i].x - side.x; pos[k + 4] = pts[i].y - side.y; pos[k + 5] = pts[i].z - side.z;
      for (let j = 0; j < 8; j += 4) { col[c4 + j] = lerp(1, 0.15, i / NTR); col[c4 + j + 1] = lerp(1, 0.84, i / NTR); col[c4 + j + 2] = lerp(1, 0.82, i / NTR); col[c4 + j + 3] = 0.85 * fade; }
    }
    trailGeo.attributes.position.needsUpdate = true; trailGeo.attributes.color.needsUpdate = true;
  }

  function updateSparks(t, f) {
    const pos = sparkGeo.attributes.position.array, col = sparkGeo.attributes.color.array;
    const onRoute = t > 1.6 && t < 11.6;
    const s = S(t);
    for (let i = 0; i < NSPARK; i++) {
      const k = i * 3;
      if (!onRoute) { pos[k + 1] = -1000; continue; }
      const back = (i + ((t * 9) % 1)) * 7; // drift backwards along the trail
      const p = routeAt(Math.max(0, s - back));
      const life = i / NSPARK;
      const ang = hash(i) * 6.283, rad = 4 + hash(i + 50) * 9;
      pos[k] = p.x + Math.cos(ang) * rad; pos[k + 2] = p.z + Math.sin(ang) * rad;
      pos[k + 1] = 2 + f.pos.y * Math.pow(1 - life, 3) * 0.8;
      const a = (1 - life) * (0.6 + 0.4 * Math.sin(t * 20 + i));
      col[k] = 0.6 * a; col[k + 1] = 1 * a; col[k + 2] = 0.98 * a;
    }
    sparkGeo.attributes.position.needsUpdate = true; sparkGeo.attributes.color.needsUpdate = true;
  }

  // Landmark pin timing: [key, in, out]
  const PIN_TIMES = [["toll", 1.55, 2.75], ["mcd", 4.05, 5.3], ["kfc", 4.55, 6.0], ["dataran", 5.85, 7.75], ["aeon", 7.5, 9.35]];

  let lastT = -1;
  function frame(t) {
    t = clamp(t, 0, 15);
    if (t === lastT) return anchors;
    lastT = t;
    const c = camAt(t);
    camera.position.copy(c.pos);
    camera.up.set(0, 1, 0);
    camera.lookAt(c.target);
    camera.updateMatrixWorld();
    camera.near = Math.max(1, c.D * 0.02); camera.far = c.D * 12; camera.updateProjectionMatrix();
    scene.fog.near = c.D * 1.25; scene.fog.far = c.D * 4.2;

    // sun + shadow frustum follow the look-at point
    sun.position.copy(c.target).addScaledVector(SUN_DIR, 2500); sun.target.position.copy(c.target);
    const ext = clamp(c.D * 0.95, 200, 1800);
    const sc = sun.shadow.camera; sc.left = -ext; sc.right = ext; sc.top = ext; sc.bottom = -ext; sc.near = 100; sc.far = 5200; sc.updateProjectionMatrix();

    const f = flyAt(t);
    setTrail(t < 1.6 ? 0 : S(t));

    // landmark pins
    for (const [k, a, b] of PIN_TIMES) {
      const u = smooth((t - a) / 0.35) * (1 - smooth((t - b) / 0.3));
      const dist = camera.position.distanceTo(pinPos[k]);
      posePin(pins[k], pinPos[k], dist * 0.022, u, t, 4.2);
      anchors[k] = u > 0.01 ? project(pins[k].head.position.clone().setY(pins[k].head.position.y + 3.4 * dist * 0.022)) : null;
    }
    // destination pin: a turquoise beacon all the way, big and pulsing on arrival
    {
      const dist = camera.position.distanceTo(P_DEST);
      const arrive = smooth((t - 10.3) / 0.5);
      const u = t < 1.3 ? 0 : smooth((t - 1.3) / 0.5);
      posePin(pins.dest, P_DEST, dist * lerp(0.02, 0.034, arrive) * (1 + 0.06 * Math.sin(t * 8) * arrive), u, t, 3.6);
      pins.dest.head.children[0].material.emissiveIntensity = 0.18 + 0.35 * arrive * (0.5 + 0.5 * Math.sin(t * 8));
      anchors.dest = project(pins.dest.head.position.clone().setY(pins.dest.head.position.y + 3.4 * dist * lerp(0.02, 0.034, arrive)));
      anchors.destGround = project(P_DEST);
    }
    // traffic lights: green lamp glows when the fly is close
    for (const L of lightModels) {
      const near = clamp(1 - Math.abs(S(t) - L.s) / 260, 0, 1);
      L.lamps[2].material.emissiveIntensity = 0.4 + 2.6 * near * (0.8 + 0.2 * Math.sin(t * 12));
      L.halo.material.opacity = 0.2 + 0.8 * near;
    }
    anchors.light = project(lightModels[0].g.localToWorld(new THREE.Vector3(9, 16, 0)));

    // turn arrows: rise out of the road, pulse, sink away
    for (const { a, t0, t1 } of arrows) {
      const u = smooth((t - t0) / 0.3) * (1 - smooth((t - (t1 - 0.3)) / 0.3));
      a.grp.visible = u > 0.001;
      a.grp.position.y = lerp(-6, 3.5, backOut(smooth((t - t0) / 0.35), 2.4)) - (1 - u) * 4;
      a.mat.opacity = u; a.glowM.material.opacity = 0.2 * u * (0.7 + 0.3 * Math.sin(t * 14));
      a.mat.emissiveIntensity = 0.25 + 0.2 * Math.sin(t * 10);
    }

    // fly shadow on the ground
    {
      const size = camera.position.distanceTo(f.pos) * FLY_SIZE(t) * 3.2;
      blob.position.set(f.pos.x, 0.95, f.pos.z); blob.scale.setScalar(size);
      blob.material.opacity = t > 1.6 && t < 11.5 ? 0.9 : smooth((t - 1.2) / 0.4) * (1 - smooth((t - 11.5) / 0.4));
    }
    updateSparks(t, f);

    renderer.render(scene, camera);

    // ---------------- fly layer (same camera; end card pins the fly next to the logo pin)
    let fp = f;
    if (t > 11.35) {
      const u = smoother((t - 11.35) / 0.9);
      const card = camPoint(c, 0.6, 0.53 + Math.sin(t * 2.2) * 0.012, c.D * 0.5); // beside the logo pin (≈ x 865, y 450)
      fp = { ...f, pos: f.pos.clone().lerp(card, u), bank: 0, pitch: 0 };
    }
    const sizeK = FLY_SIZE(t);
    poseFly(t, fp, sizeK);
    const bp = bigPinPose(t);
    bigPin.visible = bp.vis && bp.scale > 0.01;
    bigPin.position.copy(bp.pos).setY(bp.pos.y); bigPin.scale.setScalar(Math.max(0.001, bp.scale));
    bigPin.quaternion.copy(camera.quaternion); bigPin.rotateY(Math.sin(t * 2) * 0.35);
    flyKey.position.copy(fp.pos).addScaledVector(SUN_DIR, 100); flyKey.target.position.copy(fp.pos);
    flyRim.position.copy(fp.pos).add(c.h.clone().multiplyScalar(80)).add(new THREE.Vector3(0, 30, 0)); flyRim.target.position.copy(fp.pos);
    airTrail.visible = t > 0.75 && t < 11.4;
    if (airTrail.visible) updateAirTrail(t, sizeK);
    flyRenderer.render(flyScene, camera);
    anchors.fly = project(fp.pos);
    return anchors;
  }

  // Time at which the fly reaches distance s along the route (bisection on the monotone S curve).
  function tAtS(s) { let a = 1.3, b = 10.62; for (let i = 0; i < 40; i++) { const m = (a + b) / 2; if (S(m) < s) a = m; else b = m; } return b; }
  window.World = { frame, camera, tAtS, S_LANDMARK: { mcd: LM.mcd.s, kfc: S_LEFT1, dataran: LM.dataran.s, aeon: LM.aeon.s } };
})();
