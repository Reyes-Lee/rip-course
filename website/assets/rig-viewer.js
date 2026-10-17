// 首頁的 3D 機台：載入 pendulum_rig.glb，用簡化的旋轉倒單擺物理＋控制器
// 帶動 arm（繞垂直軸）與 pendulum（繞手臂方向），循環「垂下 → 甩上 → 平衡 → 放手」。
// 物理參數取自 model.urdf（10 元硬幣外貼）；控制器增益先在 Python 模擬調過。
import * as THREE from "./vendor/three/build/three.module.min.js";
import { GLTFLoader } from "./vendor/three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "./vendor/three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "./vendor/three/examples/jsm/environments/RoomEnvironment.js";

const MODEL_URL = new URL("models/pendulum_rig.glb", import.meta.url).href;

// ---- 物理（θ = 0 直立，π 垂下；α = 手臂角；u = 手臂角加速度）----
const M = 0.01438, D = 0.05139, R = 0.062, G = 9.81;
const IP = 8.698e-6 + M * D * D;
const VISC = 1.0e-5, COUL = 1.8e-5;
const A_MAX = 150;                                   // rad/s²，同策略上限
const K_LQR = [-931.085, -75.325, -50.0, -27.175];   // [θ, θ̇, α, α̇]
const SWING = { ke: 2500, aMax: 50, kp: 20, kd: 10 };
const SWAY = 0.5;                                    // 鏡頭左右晃動幅度（rad，約 ±29°）
const HANG_S = 1.2, BALANCE_S = 6.5, DROP_S = 4.5;

const wrap = (x) => ((x + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI;
const clamp = (x, a) => Math.max(-a, Math.min(a, x));

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
    // 放手後加一點額外阻尼，讓它在循環內停下來
    const damp = this.mode === "drop" ? 2.5e-5 : 0;
    const thdd = (M * G * D * Math.sin(this.th) - M * D * R * Math.cos(this.th) * u
      - (VISC + damp) * this.thd - COUL * Math.sign(this.thd)) / IP;
    this.thd += thdd * dt; this.th += this.thd * dt;
    this.ald += u * dt; this.al += this.ald * dt;
    this.t += dt; this.tMode += dt;
  }
}

const LABEL = { hang: "READY", swing: "SWING-UP", balance: "BALANCING", drop: "RELEASE" };

function mount(host) {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canvas = document.createElement("canvas");
  canvas.className = "rip-rig__canvas";
  host.appendChild(canvas);
  const hud = host.querySelector(".rip-rig__hud");

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
  key.shadow.camera.left = key.shadow.camera.bottom = -0.3;
  key.shadow.camera.right = key.shadow.camera.top = 0.3;
  key.shadow.radius = 6;
  scene.add(key, new THREE.HemisphereLight(0xffe6f2, 0x1a1430, 0.6));

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 1.5), new THREE.ShadowMaterial({ opacity: 0.35 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  const rig = new Rig();
  host.rig = rig;                          // 方便在瀏覽器主控台檢查狀態
  let fit = () => {};
  let arm = null, pend = null, running = true, visible = true, raf = 0, last = performance.now();

  new GLTFLoader().load(MODEL_URL, (gltf) => {
    const root = gltf.scene;
    root.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(root);
    arm = root.getObjectByName("arm");
    pend = root.getObjectByName("pendulum");
    // 鏡頭範圍：底座的外框，加上「擺錘直立、手臂轉到 −1／0／+1 rad」時手臂與擺錘的外框。
    // 分零件算比整台的外框緊，不會把麵包板上方的空中也算進去。
    const pts = [];
    const addBox = (obj) => {
      const b = new THREE.Box3().setFromObject(obj);
      for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) pts.push(new THREE.Vector3(x, y, z));
    };
    const base = root.getObjectByName("base");
    root.updateMatrixWorld(true);
    addBox(base);
    pend.rotation.x = Math.PI;
    for (const a of [-1, 0, 1]) { arm.rotation.y = a; root.updateMatrixWorld(true); addBox(pend); addBox(arm); }
    arm.rotation.y = 0; pend.rotation.x = 0; root.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromPoints(pts);
    const center = box.getCenter(new THREE.Vector3());
    const baseDir = new THREE.Vector3(0.62, 0.30, 0.78).normalize();
    fit = () => {
      // 在晃動範圍內取三個方位，二分搜尋最近的距離，讓所有點都落在畫面 88% 以內。
      const cam = camera.clone();
      const ok = (d) => [-SWAY, 0, SWAY].every((az) => {
        const dir = baseDir.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), az);
        cam.position.copy(center).addScaledVector(dir, d);
        cam.lookAt(center); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
        return pts.every((p) => { const q = p.clone().project(cam); return Math.abs(q.x) < 0.88 && Math.abs(q.y) < 0.88; });
      });
      const solve = () => {
        let lo = 0.05, hi = 3;
        for (let i = 0; i < 30; i++) { const mid = (lo + hi) / 2; if (ok(mid)) hi = mid; else lo = mid; }
        return hi;
      };
      // 先求距離，再把畫面中心移到模型投影的中心（上下左右留白平均），重算兩次
      for (let k = 0; k < 2; k++) {
        const d = solve();
        cam.position.copy(center).addScaledVector(baseDir, d);
        cam.lookAt(center); cam.updateMatrixWorld();
        let x0 = 1, x1 = -1, y0 = 1, y1 = -1;
        for (const p of pts) { const q = p.clone().project(cam); x0 = Math.min(x0, q.x); x1 = Math.max(x1, q.x); y0 = Math.min(y0, q.y); y1 = Math.max(y1, q.y); }
        const mid = new THREE.Vector3((x0 + x1) / 2, (y0 + y1) / 2, new THREE.Vector3().copy(center).project(cam).z).unproject(cam);
        center.copy(mid);
      }
      camera.position.copy(center).addScaledVector(baseDir, solve());
      controls.target.copy(center);
    };
    controls.target.copy(center);
    fit();
    controls.update();
    host.classList.add("is-ready");
  }, undefined, () => host.classList.add("is-failed"));

  function resize() {
    const w = host.clientWidth, h = host.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    fit();
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
    if (arm && pend) {
      if (reduce) {
        arm.rotation.y = 0; pend.rotation.x = Math.PI;   // 靜態：直立
      } else {
        const n = Math.ceil(dt / 0.001);
        for (let i = 0; i < n; i++) rig.step(dt / n);
        arm.rotation.y = rig.al;
        pend.rotation.x = Math.PI - rig.th;
        if (hud) {
          hud.dataset.mode = rig.mode;
          hud.querySelector("b").textContent = LABEL[rig.mode];
          hud.querySelector("span").textContent = `θ ${(wrap(rig.th) * 180 / Math.PI).toFixed(1).padStart(6)}°`;
        }
      }
    }
    // 角速度 = 0.1047·speed rad/s；取 speed = SWAY·ω/0.1047·cos(ωt) 得到 ±SWAY 的正弦晃動
    const w = (2 * Math.PI) / 16;
    controls.autoRotateSpeed = (SWAY * w / 0.1047) * Math.cos(w * now / 1000);
    controls.update(dt);
    renderer.render(scene, camera);
  }
  raf = requestAnimationFrame(frame);

  return () => {
    cancelAnimationFrame(raf);
    ro.disconnect(); io.disconnect();
    controls.dispose(); pmrem.dispose(); renderer.dispose();
    canvas.remove();
    host.classList.remove("is-ready");
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
