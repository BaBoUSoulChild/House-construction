import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const viewport = document.getElementById("viewport");
const dropzone = document.getElementById("dropzone");
const emptyHint = document.getElementById("empty-hint");

// --- Scene / camera / renderer ---------------------------------------------

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1b1d22);

const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.01, 1000);
camera.position.set(3, 2.2, 4);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
viewport.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.9, 0);
controls.enableDamping = true;

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// --- Lights ------------------------------------------------------------------

scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const sun = new THREE.DirectionalLight(0xffffff, 1.5);
sun.position.set(4, 6, 3);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = -6;
sun.shadow.camera.right = 6;
sun.shadow.camera.top = 6;
sun.shadow.camera.bottom = -6;
scene.add(sun);

const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(40, 40),
  new THREE.MeshStandardMaterial({ color: 0x22252c, roughness: 1 })
);
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
scene.add(floor);

let gridHelper = new THREE.GridHelper(10, 10, 0x555555, 0x333333);
scene.add(gridHelper);

// --- Human silhouette for scale reference -------------------------------------

function makeSilhouette() {
  const TOTAL_HEIGHT = 1.75;
  const bodyRadius = 0.15;
  const headRadius = 0.115;
  const bodyHeight = TOTAL_HEIGHT - 2 * headRadius; // feet to top of shoulders
  const cylinderLength = bodyHeight - 2 * bodyRadius;

  const group = new THREE.Group();
  const material = new THREE.MeshStandardMaterial({ color: 0x6ea8fe, transparent: true, opacity: 0.35 });
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(bodyRadius, cylinderLength, 4, 12), material);
  body.position.y = bodyHeight / 2;
  body.castShadow = true;
  const head = new THREE.Mesh(new THREE.SphereGeometry(headRadius, 16, 16), material);
  head.position.y = bodyHeight + headRadius; // sits on top of the body, not buried in it
  head.castShadow = true;
  group.add(body, head);
  group.position.x = -1.2;
  return group;
}
const silhouette = makeSilhouette();
silhouette.visible = false;
scene.add(silhouette);

document.getElementById("toggle-silhouette").addEventListener("click", (e) => {
  silhouette.visible = !silhouette.visible;
  e.target.classList.toggle("active", silhouette.visible);
});
document.getElementById("toggle-grid").addEventListener("click", (e) => {
  gridHelper.visible = !gridHelper.visible;
  e.target.classList.toggle("active", gridHelper.visible);
});

// --- Model loading -------------------------------------------------------------

let furnitureGroup = new THREE.Group();
scene.add(furnitureGroup);
const meshByPanelName = new Map();
let highlightedPanel = null;
const baseMaterialColor = new Map();

// Marqueurs rouges de quincaillerie (vis, tourillons...) + panneaux surlignés en rouge.
let markersGroup = new THREE.Group();
scene.add(markersGroup);
const markerGeometry = new THREE.SphereGeometry(0.012, 12, 12);
const markerMaterial = new THREE.MeshStandardMaterial({ color: 0xff2a2a, emissive: 0x661010 });
let hardwareHighlightedPanels = [];

function clearFurniture() {
  scene.remove(furnitureGroup);
  furnitureGroup = new THREE.Group();
  scene.add(furnitureGroup);
  meshByPanelName.clear();
  baseMaterialColor.clear();
  highlightedPanel = null;
  clearHardwareHighlight();
}

function clearPanelHighlight() {
  if (highlightedPanel) {
    highlightedPanel.material.emissive?.setHex(0x000000);
    highlightedPanel = null;
  }
  document.querySelectorAll("#panels-list li.active").forEach((li) => li.classList.remove("active"));
}

function clearHardwareHighlight() {
  for (const mesh of hardwareHighlightedPanels) {
    mesh.material.emissive?.setHex(0x000000);
  }
  hardwareHighlightedPanels = [];
  scene.remove(markersGroup);
  markersGroup = new THREE.Group();
  scene.add(markersGroup);
  document.querySelectorAll("#hardware-list li.active").forEach((li) => li.classList.remove("active"));
}

function loadModel(data) {
  clearFurniture();

  document.getElementById("furniture-name").textContent = data.name || "Meuble sans nom";
  document.getElementById("furniture-desc").textContent = data.description || "";
  emptyHint.style.display = "none";

  const [ox, oy, oz] = data.overall_size_m || [0, 0, 0];
  const [omx, omy, omz] = data.overall_size_mm || [0, 0, 0];
  const stats = document.getElementById("stats");
  stats.innerHTML = "";
  const addStat = (label, value) => {
    const row = document.createElement("div");
    row.className = "stat";
    row.innerHTML = `<span>${label}</span><span>${value}</span>`;
    stats.appendChild(row);
  };
  addStat("Largeur × hauteur × profondeur", `${omx.toFixed(0)} × ${omy.toFixed(0)} × ${omz.toFixed(0)} mm`);
  addStat("Surface bois", `${(data.total_wood_area_m2 ?? 0).toFixed(2)} m²`);
  addStat("Coût bois", `${(data.total_wood_cost_eur ?? 0).toFixed(2)} €`);
  addStat("Coût quincaillerie", `${(data.total_hardware_cost_eur ?? 0).toFixed(2)} €`);
  addStat("Coût total estimé", `${(data.total_cost_eur ?? 0).toFixed(2)} €`);

  const list = document.getElementById("panels-list");
  list.innerHTML = "";

  for (const p of data.panels || []) {
    const [sx, sy, sz] = p.size_m;
    const geometry = new THREE.BoxGeometry(sx, sy, sz);
    const material = new THREE.MeshStandardMaterial({ color: p.color || "#c9a876", roughness: 0.8 });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;

    const [px, py, pz] = p.position_m;
    mesh.position.set(px, py, pz);

    const [rx, ry, rz] = (p.rotation_deg || [0, 0, 0]).map((d) => (d * Math.PI) / 180);
    mesh.rotation.set(rx, ry, rz, "ZYX");

    const edges = new THREE.LineSegments(
      new THREE.EdgesGeometry(geometry),
      new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.25 })
    );
    mesh.add(edges);

    mesh.userData.panel = p;
    furnitureGroup.add(mesh);
    meshByPanelName.set(p.name, mesh);
    baseMaterialColor.set(mesh, material.color.clone());

    const li = document.createElement("li");
    li.innerHTML = `<div>${p.name}</div><div class="dims">${(sx * 1000).toFixed(0)} × ${(sy * 1000).toFixed(0)} × ${(sz * 1000).toFixed(0)} mm — ${p.material}</div>`;
    li.addEventListener("click", () => selectPanel(p.name));
    li.dataset.panel = p.name;
    list.appendChild(li);
  }

  const hardwareList = document.getElementById("hardware-list");
  hardwareList.innerHTML = "";
  for (const h of data.hardware || []) {
    const hasPositions = (h.positions_m || []).length > 0;
    const li = document.createElement("li");
    li.classList.toggle("disabled", !hasPositions);
    const priceTxt = h.unit_price ? ` — ${h.unit_price.toFixed(2)} €/u` : "";
    const hint = hasPositions
      ? '<div class="hint">cliquer pour localiser en 3D</div>'
      : '<div class="hint">emplacement non renseigné</div>';
    li.innerHTML = `<div>${h.name} <span class="qty">× ${h.qty}${priceTxt}</span></div>${hint}`;
    li.dataset.hardware = h.name;
    if (hasPositions) {
      li.addEventListener("click", () => selectHardware(h.name, data.hardware));
    }
    hardwareList.appendChild(li);
  }

  // Frame camera on the furniture's bounding box.
  const box = new THREE.Box3().setFromObject(furnitureGroup);
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);
  const radius = Math.max(size.length() * 0.6, 0.5);
  controls.target.copy(center);
  camera.position.copy(center).add(new THREE.Vector3(radius, radius * 0.7, radius));
  camera.near = radius / 100;
  camera.far = radius * 100;
  camera.updateProjectionMatrix();

  const gridSize = Math.max(10, Math.ceil((Math.max(size.x, size.z) + 4) / 2) * 2);
  const wasVisible = gridHelper.visible;
  scene.remove(gridHelper);
  gridHelper = new THREE.GridHelper(gridSize, gridSize, 0x555555, 0x333333);
  gridHelper.visible = wasVisible;
  scene.add(gridHelper);
}

function selectPanel(name) {
  clearHardwareHighlight();
  clearPanelHighlight();
  document.querySelectorAll("#panels-list li").forEach((li) => li.classList.toggle("active", li.dataset.panel === name));
  const mesh = meshByPanelName.get(name);
  if (mesh) {
    mesh.material.emissive = new THREE.Color(0x6ea8fe);
    mesh.material.emissiveIntensity = 0.5;
    highlightedPanel = mesh;
  }
}

function selectHardware(name, hardwareData) {
  clearPanelHighlight();
  clearHardwareHighlight();
  document.querySelectorAll("#hardware-list li").forEach((li) => {
    li.classList.toggle("active", li.dataset.hardware === name);
  });

  const entry = (hardwareData || []).find((h) => h.name === name);
  if (!entry) return;

  for (const panelName of entry.panels || []) {
    const mesh = meshByPanelName.get(panelName);
    if (mesh) {
      mesh.material.emissive = new THREE.Color(0xff2a2a);
      mesh.material.emissiveIntensity = 0.4;
      hardwareHighlightedPanels.push(mesh);
    }
  }

  for (const [mx, my, mz] of entry.positions_m || []) {
    const marker = new THREE.Mesh(markerGeometry, markerMaterial);
    marker.position.set(mx, my, mz);
    markersGroup.add(marker);
  }
}

// Click-to-select in the 3D view.
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
renderer.domElement.addEventListener("click", (event) => {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  // recursive:false — furnitureGroup.children are already the panel meshes;
  // going recursive would also raycast their EdgesGeometry outline children,
  // whose default line-picking threshold (1 world unit) is larger than the
  // whole furniture and drowns out the real box-face hits.
  const hits = raycaster.intersectObjects(furnitureGroup.children, false);
  if (hits.length > 0 && hits[0].object.userData.panel) {
    selectPanel(hits[0].object.userData.panel.name);
  }
});

// --- Loading sources: ?model=..., drag & drop, file picker --------------------

async function loadFromUrl(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Impossible de charger ${url} (${res.status})`);
  loadModel(await res.json());
}

document.getElementById("file-input").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (file) readFile(file);
});

function readFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      loadModel(JSON.parse(reader.result));
    } catch (err) {
      alert("Fichier JSON invalide : " + err.message);
    }
  };
  reader.readAsText(file);
}

["dragenter", "dragover"].forEach((evt) =>
  window.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("visible");
  })
);
["dragleave", "drop"].forEach((evt) =>
  window.addEventListener(evt, (e) => {
    e.preventDefault();
    if (evt === "dragleave" && e.target !== dropzone) return;
    dropzone.classList.remove("visible");
  })
);
window.addEventListener("drop", (e) => {
  const file = e.dataTransfer?.files?.[0];
  if (file) readFile(file);
});

const params = new URLSearchParams(window.location.search);
const modelParam = params.get("model");
if (modelParam) {
  loadFromUrl(modelParam).catch((err) => {
    console.error(err);
    emptyHint.textContent = `Erreur de chargement de "${modelParam}" : ${err.message}`;
  });
}

// --- Render loop ---------------------------------------------------------------

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();
