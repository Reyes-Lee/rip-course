// 首頁的 3D 機台：載入 pendulum_rig.glb，先用一塊絲絨布蓋住（真的布料物理），
// 使用者用滑鼠或手指把布拉掉之後，鏡頭推近，擺錘開始「垂下 → 甩上 → 平衡 → 放手」循環。
// 擺錘物理參數取自 model.urdf（10 元硬幣外貼）；控制器增益先在 Python 模擬調過。
import * as THREE from "./vendor/three/build/three.module.min.js";
import { GLTFLoader } from "./vendor/three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "./vendor/three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "./vendor/three/examples/jsm/environments/RoomEnvironment.js";

const MODEL_URL = new URL("models/pendulum_rig.glb", import.meta.url).href;

// ---- 擺錘物理（θ = 0 直立，π 垂下；α = 手臂角；u = 手臂角加速度）----
const M = 0.01438, D = 0.05139, R = 0.062, G = 9.81;
const IP = 8.698e-6 + M * D * D;
const VISC = 1.0e-5, COUL = 1.8e-5;
const A_MAX = 150;                                   // rad/s²，同策略上限
const K_LQR = [-931.085, -75.325, -50.0, -27.175];   // [θ, θ̇, α, α̇]
const SWING = { ke: 2500, aMax: 50, kp: 20, kd: 10 };
const SWAY = 0.5;                                    // 鏡頭左右晃動幅度（rad，約 ±29°）
const HANG_S = 1.2, BALANCE_S = 6.5, DROP_S = 4.5;
// 布的重心被拉離原位超過這個距離（公尺）才接自動抽走：大約是機台大半都露出來了
const REVEAL_SHIFT = 0.14;

const wrap = (x) => ((x + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI;
const clamp = (x, a) => Math.max(-a, Math.min(a, x));
const smooth = (t) => t * t * (3 - 2 * t);

class Rig {
  constructor() { this.reset(); }
  reset() {
    this.th = Math.PI - 0.03; this.thd = 0; this.al = 0; this.ald = 0;
    this.mode = "hang"; this.t = 0; this.tMode = 0; this.pushed = false;
  }
  setMode(m) { this.mode = m; this.tMode = 0; }
  step(dt) {
    const e = wrap(this.th);
    const E = 0.5 * IP * this.thd ** 2 + M * G * D * (Math.cos(this.th) - 1);
    let u = 0;
    if (this.mode === "hang") {
      if (this.tMode > HANG_S) this.setMode("swing");
    } else if (this.mode === "swing") {
      u = clamp(SWING.ke * E * this.thd * Math.cos(this.th), SWING.aMax) - SWING.kp * this.al - SWING.kd * this.ald;
      if (Math.abs(e) < 0.35 && Math.abs(this.thd) < 6) this.setMode("balance");
      if (this.tMode > 12) this.reset();
    } else if (this.mode === "balance") {
      u = -(K_LQR[0] * e + K_LQR[1] * this.thd + K_LQR[2] * this.al + K_LQR[3] * this.ald);
      if (!this.pushed && this.tMode > 3.2) { this.thd += 1.6; this.pushed = true; }  // 推一下，看它救回來
      if (this.tMode > BALANCE_S) this.setMode("drop");
    } else if (this.mode === "drop") {
      u = -25 * this.al - 10 * this.ald;
      if (this.tMode > DROP_S) this.reset();
    }
    u = clamp(u, A_MAX);
    const damp = this.mode === "drop" ? 2.5e-5 : 0;     // 放手後多一點阻尼，在循環內停下來
    const thdd = (M * G * D * Math.sin(this.th) - M * D * R * Math.cos(this.th) * u
      - (VISC + damp) * this.thd - COUL * Math.sign(this.thd)) / IP;
    this.thd += thdd * dt; this.th += this.thd * dt;
    this.ald += u * dt; this.al += this.ald * dt;
    this.t += dt; this.tMode += dt;
  }
}

const LABEL = { hang: "READY", swing: "SWING-UP", balance: "BALANCING", drop: "RELEASE" };

// ---- 布料：Verlet 質點＋距離約束，與機台的外框（圓角盒）碰撞 ----
class Cloth {
  constructor({ nx, nz, sx, sz, cx, cz, y }) {
    this.nx = nx; this.nz = nz;
    const n = nx * nz;
    this.pos = new Float32Array(n * 3);
    this.prev = new Float32Array(n * 3);
    this.inv = new Float32Array(n).fill(1);
    this.dx = sx / (nx - 1); this.dz = sz / (nz - 1);
    this.layout = { sx, sz, cx, cz };
    this.layFlat(y);
    const c = [];
    const add = (a, b, s) => {
      const ax = a * 3, bx = b * 3;
      c.push(a, b, Math.hypot(this.pos[ax] - this.pos[bx], this.pos[ax + 1] - this.pos[bx + 1], this.pos[ax + 2] - this.pos[bx + 2]), s);
    };
    const id = (i, j) => j * nx + i;
    for (let j = 0; j < nz; j++) for (let i = 0; i < nx; i++) {
      if (i < nx - 1) add(id(i, j), id(i + 1, j), 1);          // 結構
      if (j < nz - 1) add(id(i, j), id(i, j + 1), 1);
      if (i < nx - 1 && j < nz - 1) { add(id(i, j), id(i + 1, j + 1), 0.6); add(id(i + 1, j), id(i, j + 1), 0.6); }  // 剪切
      if (i < nx - 2) add(id(i, j), id(i + 2, j), 0.18);        // 彎曲：讓布有一點硬挺感，皺褶比較大
      if (j < nz - 2) add(id(i, j), id(i, j + 2), 0.18);
    }
    this.con = new Float32Array(c);
    this.boxes = [];
    this.wind = 0;
    this.grip = true;             // 揭開時關掉，布才滑得走
  }
  // 把布攤平在高度 y（一點點不平整，落下時才會有自然的皺褶）
  layFlat(y) {
    const { nx, nz } = this, { sx, sz, cx, cz } = this.layout;
    for (let j = 0; j < nz; j++) for (let i = 0; i < nx; i++) {
      const k = (j * nx + i) * 3;
      this.pos[k] = cx - sx / 2 + i * this.dx;
      this.pos[k + 1] = y + 0.006 * Math.sin(i * 0.55 + j * 0.2) * Math.cos(j * 0.45);
      this.pos[k + 2] = cz - sz / 2 + j * this.dz;
    }
    this.prev.set(this.pos);
    this.inv.fill(1);
  }
  centroid() {
    let x = 0, y = 0, z = 0;
    const n = this.inv.length;
    for (let p = 0; p < n; p++) { x += this.pos[p * 3]; y += this.pos[p * 3 + 1]; z += this.pos[p * 3 + 2]; }
    return new THREE.Vector3(x / n, y / n, z / n);
  }
  step(dt, { damping = 0.985, iters = 4, gravity = -9.81, time = 0 } = {}) {
    const { pos, prev, inv } = this;
    const n = inv.length;
    const g = gravity * dt * dt;
    for (let p = 0; p < n; p++) {
      if (inv[p] === 0) continue;
      const k = p * 3;
      // 微風：只在揭開前給一點點起伏，讓布看起來是活的
      const w = this.wind * Math.sin(time * 1.7 + pos[k] * 23 + pos[k + 2] * 17) * dt * dt;
      for (let a = 0; a < 3; a++) {
        const v = (pos[k + a] - prev[k + a]) * damping;
        prev[k + a] = pos[k + a];
        pos[k + a] += v + (a === 1 ? g + w : 0);
      }
    }
    const con = this.con;
    for (let it = 0; it < iters; it++) {
      for (let c = 0; c < con.length; c += 4) {
        const a = con[c] * 3, b = con[c + 1] * 3, rest = con[c + 2], s = con[c + 3];
        const wa = inv[con[c]], wb = inv[con[c + 1]];
        const w = wa + wb;
        if (w === 0) continue;
        const ex = pos[b] - pos[a], ey = pos[b + 1] - pos[a + 1], ez = pos[b + 2] - pos[a + 2];
        const d = Math.sqrt(ex * ex + ey * ey + ez * ez) || 1e-9;
        const f = ((d - rest) / d) * s / w;
        pos[a] += ex * f * wa; pos[a + 1] += ey * f * wa; pos[a + 2] += ez * f * wa;
        pos[b] -= ex * f * wb; pos[b + 1] -= ey * f * wb; pos[b + 2] -= ez * f * wb;
      }
      // 每一輪約束後都做碰撞，約束才不會一次把布拉進零件裡（穿模）；摩擦只在最後一輪算
      this.collide(it === iters - 1);
    }
  }
  collide(friction = true) {
    const { pos, prev, inv, boxes } = this;
    const FR = 0.35;                                   // 接觸時的摩擦
    for (let p = 0; p < inv.length; p++) {
      const k = p * 3;                                  // 被抓住的質點也要碰撞，手不能把布按進機台裡
      let x = pos[k], y = pos[k + 1], z = pos[k + 2];
      if (y < 0.0015) {                                 // 桌面
        y = 0.0015;
        if (friction) {
        prev[k] = x - (x - prev[k]) * (1 - FR * 1.6);
        prev[k + 2] = z - (z - prev[k + 2]) * (1 - FR * 1.6);
        prev[k + 1] = y;
        }
      }
      for (let b = 0; b < boxes.length; b++) {
        const B = boxes[b];
        if (x <= B[0] || x >= B[3] || y <= B[1] || y >= B[4] || z <= B[2] || z >= B[5]) continue;
        // 推回質點「上一步所在的那一側」；上一步也在裡面才退而求其次推到最近的面。
        // 不能只看最近的面：布很重時約束會一次把質點拉進零件很深，會被錯推到側面而滑掉。
        const d0 = x - B[0], d1 = B[3] - x, d2 = y - B[1], d3 = B[4] - y, d4 = z - B[2], d5 = B[5] - z;
        const py = prev[k + 1], px = prev[k], pz = prev[k + 2];
        let m;
        if (py >= B[4] - 1e-4) m = d3;
        else if (px <= B[0]) m = d0; else if (px >= B[3]) m = d1;
        else if (pz <= B[2]) m = d4; else if (pz >= B[5]) m = d5;
        else m = Math.min(d0, d1, d2, d3, d4, d5);
        if (m === d3) y = B[4]; else if (m === d0) x = B[0]; else if (m === d1) x = B[3];
        else if (m === d4) z = B[2]; else if (m === d5) z = B[5]; else y = B[1];
        if (!friction) continue;
        // 壓在零件頂面上的布摩擦大很多（絲絨會「卡」住），才不會從手臂上滑下去
        const fr = m === d3 ? (this.grip ? 0.85 : 0.2) : FR;
        if (m === d3) {
          // 靜摩擦：這一步的水平位移（含約束拉動）也打折，布才不會被四周垂下的重量拖走
          x = prev[k] + (x - prev[k]) * (1 - fr);
          z = prev[k + 2] + (z - prev[k + 2]) * (1 - fr);
        }
        prev[k] = x - (x - prev[k]) * (1 - fr);
        prev[k + 1] = y - (y - prev[k + 1]) * (1 - fr);
        prev[k + 2] = z - (z - prev[k + 2]) * (1 - fr);
      }
      pos[k] = x; pos[k + 1] = y; pos[k + 2] = z;
    }
  }
  nearest(v) {
    let best = 0, bd = Infinity;
    for (let p = 0; p < this.inv.length; p++) {
      const k = p * 3;
      const d = (this.pos[k] - v.x) ** 2 + (this.pos[k + 1] - v.y) ** 2 + (this.pos[k + 2] - v.z) ** 2;
      if (d < bd) { bd = d; best = p; }
    }
    return best;
  }
  // 抓住的那一點附近 2 圈的質點一起帶著走（像用手捏住一把布）
  patch(p, r = 2) {
    const i0 = p % this.nx, j0 = Math.floor(p / this.nx), out = [];
    for (let j = j0 - r; j <= j0 + r; j++) for (let i = i0 - r; i <= i0 + r; i++) {
      if (i < 0 || j < 0 || i >= this.nx || j >= this.nz) continue;
      const k = j * this.nx + i;
      const kk = k * 3, pk = p * 3;
      out.push([k, this.pos[kk] - this.pos[pk], this.pos[kk + 1] - this.pos[pk + 1], this.pos[kk + 2] - this.pos[pk + 2], 1 - Math.hypot(i - i0, j - j0) / (r + 1.5)]);
    }
    return out;
  }
}

// 絲絨的貼圖：深紫黑底＋細織紋、金色雙線滾邊、頂上一行金色字
function velvetMaps() {
  const S = 1024;
  const col = document.createElement("canvas"); col.width = col.height = S;
  const met = document.createElement("canvas"); met.width = met.height = S;
  const c = col.getContext("2d"), m = met.getContext("2d");
  const grd = c.createRadialGradient(S / 2, S / 2, S * 0.1, S / 2, S / 2, S * 0.75);
  grd.addColorStop(0, "#1c0f30"); grd.addColorStop(1, "#0d0717");
  c.fillStyle = grd; c.fillRect(0, 0, S, S);
  const img = c.getImageData(0, 0, S, S);
  for (let i = 0; i < img.data.length; i += 4) {          // 細微織紋雜訊
    const n = (Math.random() - 0.5) * 10 + ((i / 4) % 4 < 2 ? 3 : -3);
    img.data[i] += n; img.data[i + 1] += n * 0.6; img.data[i + 2] += n;
  }
  c.putImageData(img, 0, 0);
  m.fillStyle = "#000"; m.fillRect(0, 0, S, S);
  const gold = (ctx, isMetal) => {
    ctx.strokeStyle = isMetal ? "#fff" : "#d6a54a";
    ctx.lineWidth = 7; ctx.strokeRect(34, 34, S - 68, S - 68);
    ctx.lineWidth = 3; ctx.strokeRect(56, 56, S - 112, S - 112);
    ctx.fillStyle = isMetal ? "#fff" : "#e0b45a";
    ctx.font = "88px Anton, Impact, sans-serif";
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.save(); ctx.translate(S / 2, S / 2); ctx.scale(1, 1.35);
    ctx.fillText("SIM2REAL", 0, 0);
    ctx.restore();
    ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(S / 2 - 210, S / 2 + 82); ctx.lineTo(S / 2 + 210, S / 2 + 82); ctx.stroke();
  };
  gold(c, false); gold(m, true);
  const tc = new THREE.CanvasTexture(col); tc.colorSpace = THREE.SRGBColorSpace; tc.anisotropy = 8;
  const tm = new THREE.CanvasTexture(met); tm.anisotropy = 8;
  return { map: tc, metal: tm };
}

function mount(host) {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canvas = document.createElement("canvas");
  canvas.className = "rip-rig__canvas";
  host.appendChild(canvas);
  const hud = host.querySelector(".rip-rig__hud");
  let hint = null;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;

  const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 10);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.enableZoom = false;
  controls.autoRotate = !reduce;
  controls.autoRotateSpeed = 0;      // 每一幀依時間改正負，變成左右晃
  controls.minPolarAngle = 0.35;
  controls.maxPolarAngle = 1.45;

  const key = new THREE.DirectionalLight(0xffffff, 2.2);
  key.position.set(0.4, 0.8, 0.5);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.camera.left = key.shadow.camera.bottom = -0.35;
  key.shadow.camera.right = key.shadow.camera.top = 0.35;
  key.shadow.radius = 6;
  const rim = new THREE.DirectionalLight(0xff4fa0, 0.9);      // 背後的粉紅輪廓光，讓絲絨的皺褶亮起來
  rim.position.set(-0.5, 0.35, -0.6);
  scene.add(key, rim, new THREE.HemisphereLight(0xffe6f2, 0x1a1430, 0.6));

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShadowMaterial({ opacity: 0.35 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  const rig = new Rig();
  host.rig = rig;                          // 方便在瀏覽器主控台檢查狀態
  let arm = null, pend = null, visible = true, raf = 0, last = performance.now();
  // 鏡頭：揭開前看得到整塊布（clothView），揭開後推近到機台（rigView）
  let rigPts = [], clothPts = [], rigView = null, clothView = null, viewK = reduce ? 1 : 0;
  const baseDir = new THREE.Vector3(0.62, 0.30, 0.78).normalize();

  // ---- 布幕狀態 ----
  let cloth = null, clothMesh = null, clothGeo = null;
  let phase = reduce ? "live" : "loading";   // loading → covered → pulling → flying → live → settling → dropping → covered
  let coverBtn = null, restCentroid = null, dropY = 0.2, settle = null;
  let grab = null;                             // { patch, target, plane, start, vel }
  let tPhase = 0, simTime = 0;

  function computeView(pts) {
    if (!pts.length) return null;
    const box = new THREE.Box3().setFromPoints(pts);
    const center = box.getCenter(new THREE.Vector3());
    const cam = camera.clone();
    const ok = (d) => [-SWAY, 0, SWAY].every((az) => {
      const dir = baseDir.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), az);
      cam.position.copy(center).addScaledVector(dir, d);
      cam.lookAt(center); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
      return pts.every((p) => { const q = p.clone().project(cam); return Math.abs(q.x) < 0.88 && Math.abs(q.y) < 0.88; });
    });
    const solve = () => {
      let lo = 0.05, hi = 4;
      for (let i = 0; i < 30; i++) { const mid = (lo + hi) / 2; if (ok(mid)) hi = mid; else lo = mid; }
      return hi;
    };
    // 求距離，再把中心移到投影中心（上下左右留白平均），重算兩次
    for (let k = 0; k < 2; k++) {
      const d = solve();
      cam.position.copy(center).addScaledVector(baseDir, d);
      cam.lookAt(center); cam.updateMatrixWorld();
      let x0 = 1, x1 = -1, y0 = 1, y1 = -1;
      for (const p of pts) { const q = p.clone().project(cam); x0 = Math.min(x0, q.x); x1 = Math.max(x1, q.x); y0 = Math.min(y0, q.y); y1 = Math.max(y1, q.y); }
      center.copy(new THREE.Vector3((x0 + x1) / 2, (y0 + y1) / 2, center.clone().project(cam).z).unproject(cam));
    }
    return { center, dist: solve() };
  }
  function refit() {
    rigView = computeView(rigPts);
    clothView = clothPts.length ? computeView(clothPts.concat(rigPts)) : rigView;
  }
  function applyView() {
    if (!rigView) return;
    const k = smooth(Math.min(1, viewK));
    const c = clothView.center.clone().lerp(rigView.center, k);
    const d = clothView.dist + (rigView.dist - clothView.dist) * k;
    const dir = camera.position.clone().sub(controls.target);
    if (dir.lengthSq() < 1e-9) dir.copy(baseDir);
    controls.target.copy(c);
    camera.position.copy(c).addScaledVector(dir.normalize(), d);
  }

  new GLTFLoader().load(MODEL_URL, (gltf) => {
    const root = gltf.scene;
    root.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(root);
    arm = root.getObjectByName("arm");
    pend = root.getObjectByName("pendulum");
    const base = root.getObjectByName("base");
    const corners = (b) => {
      const o = [];
      for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) o.push(new THREE.Vector3(x, y, z));
      return o;
    };
    // 機台的鏡頭範圍：底座＋「擺錘直立、手臂轉到 −1／0／+1 rad」時的手臂與擺錘
    root.updateMatrixWorld(true);
    rigPts.push(...corners(new THREE.Box3().setFromObject(base)));
    pend.rotation.x = Math.PI;
    for (const a of [-1, 0, 1]) {
      arm.rotation.y = a; root.updateMatrixWorld(true);
      rigPts.push(...corners(new THREE.Box3().setFromObject(pend)), ...corners(new THREE.Box3().setFromObject(arm)));
    }
    arm.rotation.y = 0; pend.rotation.x = 0; root.updateMatrixWorld(true);

    if (!reduce) buildCloth(root);
    refit();
    applyView();
    controls.update();
    host.classList.add("is-ready");
    if (reduce) host.classList.add("is-revealed");
  }, undefined, () => host.classList.add("is-failed"));

  function buildCloth(root) {
    // 碰撞體：每個零件的外框（太小的線材、LED 略過），外擴 3 mm 當布的厚度
    const boxes = [];
    const all = new THREE.Box3();
    root.traverse((o) => {
      if (!o.isMesh) return;
      const b = new THREE.Box3().setFromObject(o);
      all.union(b);
      const s = b.getSize(new THREE.Vector3());
      if (s.x * s.y * s.z < 2e-8 && Math.max(s.x, s.y, s.z) < 0.02) return;
      const m = 0.006;                         // 布和零件之間留 6 mm，細的零件才不會從質點之間穿出來
      boxes.push([b.min.x - m, b.min.y - m, b.min.z - m, b.max.x + m, b.max.y + m, b.max.z + m]);
    });
    const size = all.getSize(new THREE.Vector3()), mid = all.getCenter(new THREE.Vector3());
    const drop = Math.max(size.y, 0.06);
    // 布的中心往最高的零件（手臂與馬達）那側偏，手臂那一端才蓋得住
    const tall = new THREE.Box3().setFromObject(root.getObjectByName("arm"));
    const cx = mid.x * 0.55 + tall.getCenter(new THREE.Vector3()).x * 0.45;
    cloth = new Cloth({ nx: 54, nz: 40, sx: size.x + 2 * drop * 0.95, sz: size.z + 2 * drop * 0.95, cx, cz: mid.z, y: all.max.y + 0.012 });
    cloth.boxes = boxes;
    for (let i = 0; i < 520; i++) cloth.step(1 / 120, { damping: 0.97, iters: 5 });   // 先在畫面外讓布落下、蓋好
    cloth.wind = 0.35;
    restCentroid = cloth.centroid();
    dropY = all.max.y + 0.07;

    const { nx, nz } = cloth;
    clothGeo = new THREE.BufferGeometry();
    clothGeo.setAttribute("position", new THREE.BufferAttribute(cloth.pos, 3).setUsage(THREE.DynamicDrawUsage));
    const uv = new Float32Array(nx * nz * 2);
    for (let j = 0; j < nz; j++) for (let i = 0; i < nx; i++) { uv[(j * nx + i) * 2] = i / (nx - 1); uv[(j * nx + i) * 2 + 1] = 1 - j / (nz - 1); }
    clothGeo.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
    const idx = [];
    for (let j = 0; j < nz - 1; j++) for (let i = 0; i < nx - 1; i++) {
      const a = j * nx + i, b = a + 1, c = a + nx, d = c + 1;
      idx.push(a, c, b, b, c, d);
    }
    clothGeo.setIndex(idx);
    clothGeo.computeVertexNormals();
    clothGeo.computeBoundingSphere(); clothGeo.computeBoundingBox();
    const maps = velvetMaps();
    const mat = new THREE.MeshPhysicalMaterial({
      map: maps.map, metalnessMap: maps.metal, metalness: 1, roughness: 0.86,
      sheen: 1, sheenColor: new THREE.Color(0x9c4f86), sheenRoughness: 0.5,
      side: THREE.DoubleSide, transparent: false, opacity: 1,
    });
    clothMesh = new THREE.Mesh(clothGeo, mat);
    clothMesh.castShadow = true; clothMesh.receiveShadow = true;
    scene.add(clothMesh);
    // 鏡頭在揭開前要看得到整塊布
    for (let p = 0; p < nx * nz; p += 7) clothPts.push(new THREE.Vector3(cloth.pos[p * 3], cloth.pos[p * 3 + 1], cloth.pos[p * 3 + 2]));
    phase = "covered";
    controls.enableRotate = false;            // 揭開前，拖曳是拉布，不是轉鏡頭
    canvas.style.touchAction = "none";
    makeHint();
    makeCoverButton();
    // 字型載入後重畫一次貼圖（Anton 是網頁字型）
    document.fonts?.load("88px Anton").then(() => {
      const m2 = velvetMaps(); mat.map = m2.map; mat.metalnessMap = m2.metal; mat.needsUpdate = true;
    }).catch(() => {});
  }

  function makeCoverButton() {
    coverBtn = document.createElement("button");
    coverBtn.type = "button";
    coverBtn.className = "rip-rig__cover";
    coverBtn.setAttribute("aria-label", "蓋回布幕");
    coverBtn.title = "蓋回布幕";
    coverBtn.innerHTML = '<span aria-hidden="true"></span>';
    coverBtn.addEventListener("click", () => recover());
    host.appendChild(coverBtn);
  }

  function makeHint() {
    hint = document.createElement("button");
    hint.type = "button";
    hint.className = "rip-rig__hint";
    hint.innerHTML = '<span class="rip-rig__hand" aria-hidden="true"></span>拖曳布幕，揭開機台';
    hint.addEventListener("click", () => autoReveal());
    host.appendChild(hint);
  }

  // ---- 滑鼠／手指拉布 ----
  const ray = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  const setNdc = (e) => {
    const r = canvas.getBoundingClientRect();
    ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  };
  const hitCloth = () => {
    if (!clothMesh) return null;
    camera.updateMatrixWorld();             // 保險：確保用的是現在的鏡頭方向
    ray.setFromCamera(ndc, camera);
    return ray.intersectObject(clothMesh, false)[0] || null;
  };
  function startGrab(point) {
    const p = cloth.nearest(point);
    const patch = cloth.patch(p);
    const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(camera.getWorldDirection(new THREE.Vector3()).negate(), point);
    grab = { patch, target: point.clone(), plane, start: point.clone(), vel: new THREE.Vector3(), lastT: performance.now() };
    for (const [k] of grab.patch) cloth.inv[k] = 0;
    phase = "pulling";
    cloth.wind = 0;
    cloth.grip = false;
    host.classList.add("is-pulling");
  }
  function onDown(e) {
    if (phase !== "covered") return;
    setNdc(e);
    const h = hitCloth();
    if (!h) return;
    try { canvas.setPointerCapture(e.pointerId); } catch { /* 沒有對應的實體指標時（例如程式觸發）略過 */ }
    startGrab(h.point);
    e.preventDefault();
  }
  function onMove(e) {
    setNdc(e);
    if (phase === "covered") { canvas.style.cursor = hitCloth() ? "grab" : "default"; return; }
    if (phase !== "pulling" || !grab) return;
    canvas.style.cursor = "grabbing";
    camera.updateMatrixWorld();
    ray.setFromCamera(ndc, camera);
    const p = new THREE.Vector3();
    if (!ray.ray.intersectPlane(grab.plane, p)) return;
    const now = performance.now(), dt = Math.max(1, now - grab.lastT) / 1000;
    grab.vel.lerp(p.clone().sub(grab.target).divideScalar(dt), 0.35);
    grab.lastT = now;
    grab.target.copy(p);
  }
  function onUp() {
    if (phase !== "pulling") return;
    // 拉得不夠遠：放手，布落回去
    for (const [k] of grab.patch) cloth.inv[k] = 1;
    grab = null; phase = "covered"; cloth.wind = 0.35; cloth.grip = true;
    host.classList.remove("is-pulling");
    canvas.style.cursor = "grab";
  }
  canvas.addEventListener("pointerdown", onDown);
  canvas.addEventListener("pointermove", onMove);
  canvas.addEventListener("pointerup", onUp);
  canvas.addEventListener("pointercancel", onUp);

  function beginFly(vel) {
    // 順著拉的方向（手的速度＋布已經被拉走的方向）再往上一點，把布整塊帶走
    const dir = vel.clone();
    if (restCentroid && cloth) dir.addScaledVector(cloth.centroid().sub(restCentroid), 4);
    dir.y = Math.max(dir.y, 0) + dir.length() * 0.5 + 0.4;
    if (dir.lengthSq() < 1e-6) dir.set(0.3, 1, 0.4);
    grab.flyDir = dir.normalize();
    phase = "flying"; tPhase = 0;
    cloth.grip = false;
    host.classList.add("is-revealing");
    hint?.classList.add("is-gone");
  }
  function autoReveal() {
    if (phase !== "covered" || !cloth) return;
    // 從靠鏡頭那一側的上緣抓起來，往右上方拉走
    let best = 0, bs = -Infinity;
    const toCam = camera.position.clone().sub(controls.target).normalize();
    for (let p = 0; p < cloth.inv.length; p++) {
      const v = new THREE.Vector3(cloth.pos[p * 3], cloth.pos[p * 3 + 1], cloth.pos[p * 3 + 2]);
      const s = v.dot(toCam) + v.y * 2;
      if (s > bs) { bs = s; best = p; }
    }
    const pt = new THREE.Vector3(cloth.pos[best * 3], cloth.pos[best * 3 + 1], cloth.pos[best * 3 + 2]);
    startGrab(pt);
    const right = new THREE.Vector3().crossVectors(camera.up, toCam).normalize();
    beginFly(right.multiplyScalar(-0.8).add(toCam.multiplyScalar(0.4)));
  }

  function stepCloth(dt) {
    simTime += dt;
    if (phase === "pulling" && grab) {
      for (const [k, ox, oy, oz, w] of grab.patch) {
        const kk = k * 3;
        const tx = grab.target.x + ox * 0.6, ty = grab.target.y + oy * 0.6, tz = grab.target.z + oz * 0.6;
        // 抓點本身跟手走，外圈的質點有一點延遲，看起來像捏住一把布
        cloth.pos[kk] += (tx - cloth.pos[kk]) * (0.35 + 0.6 * w);
        cloth.pos[kk + 1] += (ty - cloth.pos[kk + 1]) * (0.35 + 0.6 * w);
        cloth.pos[kk + 2] += (tz - cloth.pos[kk + 2]) * (0.35 + 0.6 * w);
        cloth.prev[kk] = cloth.pos[kk]; cloth.prev[kk + 1] = cloth.pos[kk + 1]; cloth.prev[kk + 2] = cloth.pos[kk + 2];
      }
      // 一定要把布拉離機台很多（重心移開約 14 cm）才接自動抽走的動畫
      if (cloth.centroid().distanceTo(restCentroid) > REVEAL_SHIFT) beginFly(grab.vel);
    } else if (phase === "dropping") {
      // 蓋回去：布從上方淡入、自己落下蓋好，鏡頭同時拉遠
      tPhase += dt;
      const mat = clothMesh.material;
      mat.opacity = smooth(Math.min(1, tPhase / 0.45));
      if (tPhase > 0.5 && mat.transparent) { mat.transparent = false; mat.needsUpdate = true; }
      viewK = 1 - Math.min(1, tPhase / 1.4);
      if (tPhase > 2.6) {
        phase = "covered"; viewK = 0;
        cloth.wind = 0.35;
        restCentroid = cloth.centroid();
        hint?.classList.remove("is-gone");
        host.classList.remove("is-covering");
      }
    } else if (phase === "flying" && grab) {
      tPhase += dt;
      const speed = 0.25 + 1.9 * smooth(Math.min(1, tPhase / 0.55));    // 先慢後快，像一把拉起布
      grab.target.addScaledVector(grab.flyDir, speed * dt);
      for (const [k, ox, oy, oz] of grab.patch) {
        const kk = k * 3;
        cloth.pos[kk] = grab.target.x + ox * 0.5; cloth.pos[kk + 1] = grab.target.y + oy * 0.5; cloth.pos[kk + 2] = grab.target.z + oz * 0.5;
        cloth.prev[kk] = cloth.pos[kk]; cloth.prev[kk + 1] = cloth.pos[kk + 1]; cloth.prev[kk + 2] = cloth.pos[kk + 2];
      }
      viewK = Math.min(1, Math.max(0, (tPhase - 0.35) / 1.6));
      if (tPhase > 0.7 && !clothMesh.material.transparent) { clothMesh.material.transparent = true; clothMesh.material.needsUpdate = true; }
      clothMesh.material.opacity = 1 - smooth(Math.min(1, Math.max(0, (tPhase - 0.7) / 0.6)));
      if (tPhase > 1.35) finishReveal();
    }
    if (cloth) cloth.step(dt, { time: simTime });
  }
  function finishReveal() {
    // 布留著（之後還可以蓋回去），只是藏起來、不再模擬
    for (const [k] of grab.patch) cloth.inv[k] = 1;
    clothMesh.visible = false;
    grab = null;
    phase = "live";
    controls.enableRotate = true;
    canvas.style.touchAction = "pan-y";
    canvas.style.cursor = "";
    hint?.classList.add("is-gone");
    host.classList.remove("is-pulling", "is-revealing");
    host.classList.add("is-revealed");
    rig.reset();
  }
  function recover() {
    if (phase !== "live" || !cloth) return;
    // 先讓手臂回正、擺錘平順地回到垂下，布才蓋在跟碰撞體一致的姿勢上
    settle = { a0: rig.al, th0: rig.th, th1: rig.th + wrap(Math.PI - rig.th) };
    phase = "settling"; tPhase = 0;
    host.classList.remove("is-revealed");
    host.classList.add("is-covering");
  }
  function startDrop() {
    cloth.layFlat(dropY);
    cloth.grip = true; cloth.wind = 0;
    const mat = clothMesh.material;
    mat.transparent = true; mat.opacity = 0; mat.needsUpdate = true;
    clothMesh.visible = true;
    phase = "dropping"; tPhase = 0;
    controls.enableRotate = false;
    canvas.style.touchAction = "none";
  }

  function resize() {
    const w = host.clientWidth, h = host.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    refit();
    applyView();
  }
  const ro = new ResizeObserver(resize);
  ro.observe(host);
  resize();

  const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; });
  io.observe(host);

  function frame(now) {
    raf = requestAnimationFrame(frame);
    if (!visible || document.hidden) { last = now; return; }
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    if (cloth && clothMesh.visible) {
      const n = Math.max(1, Math.round(dt / (1 / 120)));
      for (let i = 0; i < n; i++) stepCloth(dt / n);
      if (clothGeo) {
        clothGeo.attributes.position.needsUpdate = true;
        clothGeo.computeVertexNormals();
        clothGeo.computeBoundingSphere();
        clothGeo.computeBoundingBox();          // 點擊判定會先用外框盒篩選，布一變形就要跟著更新
      }
    }
    if (arm && pend) {
      if (reduce) {
        arm.rotation.y = 0; pend.rotation.x = Math.PI;   // 靜態：直立
      } else if (phase === "live") {
        if (viewK < 1) viewK = Math.min(1, viewK + dt / 1.6);   // 布飛走後，鏡頭繼續推近到機台
        const n = Math.ceil(dt / 0.001);
        for (let i = 0; i < n; i++) rig.step(dt / n);
        arm.rotation.y = rig.al;
        pend.rotation.x = Math.PI - rig.th;
        if (hud) {
          hud.dataset.mode = rig.mode;
          hud.querySelector("b").textContent = LABEL[rig.mode];
          hud.querySelector("span").textContent = `θ ${(wrap(rig.th) * 180 / Math.PI).toFixed(1).padStart(6)}°`;
        }
      } else if (phase === "settling") {
        tPhase += dt;
        const k = smooth(Math.min(1, tPhase / 0.8));
        arm.rotation.y = settle.a0 * (1 - k);
        pend.rotation.x = Math.PI - (settle.th0 + (settle.th1 - settle.th0) * k);
        if (k >= 1) { arm.rotation.y = 0; pend.rotation.x = 0; startDrop(); }
      }
    }
    // 角速度 = 0.1047·speed rad/s；取 speed = SWAY·ω/0.1047·cos(ωt) 得到 ±SWAY 的正弦晃動
    const w = (2 * Math.PI) / 16;
    controls.autoRotateSpeed = (SWAY * w / 0.1047) * Math.cos(w * now / 1000) * (phase === "pulling" ? 0 : 1);
    // 粉紅背光是給絲絨的；揭開後慢慢調弱，機台的顏色才自然
    rim.intensity += ((phase === "live" ? 0.25 : 0.9) - rim.intensity) * Math.min(1, dt * 1.5);
    controls.update(dt);
    applyView();
    renderer.render(scene, camera);
  }
  raf = requestAnimationFrame(frame);

  return () => {
    cancelAnimationFrame(raf);
    ro.disconnect(); io.disconnect();
    canvas.removeEventListener("pointerdown", onDown);
    canvas.removeEventListener("pointermove", onMove);
    canvas.removeEventListener("pointerup", onUp);
    canvas.removeEventListener("pointercancel", onUp);
    controls.dispose(); pmrem.dispose(); renderer.dispose();
    canvas.remove(); hint?.remove(); coverBtn?.remove();
    host.classList.remove("is-ready", "is-revealed", "is-pulling", "is-revealing", "is-covering");
  };
}

// Material 的 instant navigation 換頁時不會重新載入腳本，所以每次換頁檢查一次。
let dispose = null;
function init() {
  if (dispose) { dispose(); dispose = null; }
  const host = document.querySelector(".rip-rig");
  if (host) dispose = mount(host);
}
if (window.document$) window.document$.subscribe(init); else init();
