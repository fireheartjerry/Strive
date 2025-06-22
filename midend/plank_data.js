let detector;
let video;
let poses = [];
let is_detecting = false;
let start_button;
let debugTextBox;
let main_color, accent_color, text_color, debug_color, good_color;
let font;
const MAX_SAMPLES = 1000;
let sampleCount = 0;
let hnhStats = { count: 0, mean: 0, M2: 0 };
let haStats = { count: 0, mean: 0, M2: 0 };
let gpStats = { count: 0, mean: 0, M2: 0 };
let armStats = { count: 0, mean: 0, M2: 0 };
let currentMetrics = null;
let collectionComplete = false;

const BENCHMARK = {
    EAR_NECK_HIP: { min: 165, max: 180 },
    HIP_ANKLE_SLOPE: { min: -0.2, max: -0.05 },
    GLOBAL_PLANK: { min: 160, max: 175 },
    ARM_ANGLE: { min: 40, max: 70 },
};
const MIN_SCORE = 0.5;

function preload() {
    font = loadFont(
        "https://cdnjs.cloudflare.com/ajax/libs/topcoat/0.8.0/font/SourceSansPro-Regular.otf"
    );
}

function setup() {
    createCanvas(640, 600);
    video = createCapture(VIDEO);
    video.size(640, 480);
    video.hide();
    tf.ready().then(() => {
        const cfg = {
            modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING,
        };
        poseDetection
            .createDetector(poseDetection.SupportedModels.MoveNet, cfg)
            .then((d) => (detector = d));
    });
    main_color = color(41, 128, 185);
    accent_color = color(231, 76, 60);
    text_color = color(236, 240, 241);
    debug_color = color(255, 235, 59);
    good_color = color(46, 204, 113);
    start_button = createButton("START COLLECTION");
    start_button.position(10, 10);
    start_button.size(200, 50);
    start_button.style("background-color", "#2980b9");
    start_button.style("color", "white");
    start_button.style("border", "none");
    start_button.style("border-radius", "25px");
    start_button.style("font-size", "18px");
    start_button.style("font-weight", "bold");
    start_button.style("cursor", "pointer");
    start_button.mousePressed(toggleCollection);
    debugTextBox = createElement("textarea");
    debugTextBox.attribute("rows", "6");
    debugTextBox.attribute("cols", "80");
    debugTextBox.position(10, 500);
    textFont(font);
}

function draw() {
    background(0);
    image(video, 0, 0);
    if (detector && is_detecting && sampleCount < MAX_SAMPLES) detectPose();
    drawOverlay();
    updateDebugTextBox();
    if (collectionComplete) drawSummaryPanel();
}

async function detectPose() {
    const est = await detector.estimatePoses(video.elt);
    if (!is_detecting) return;
    poses = est;
    if (poses.length > 0 && !collectionComplete) {
        let m = measurePlankMetrics(poses[0]);
        currentMetrics = m;
        addSample(hnhStats, m.enh_angle);
        addSample(haStats, m.ha_slope);
        addSample(gpStats, m.global_angle);
        addSample(armStats, m.arm_angle);
        sampleCount++;
        if (sampleCount >= MAX_SAMPLES) {
            collectionComplete = true;
            is_detecting = false;
            start_button.html("RESUME COLLECTION");
        }
    }
}

function drawOverlay() {
    if (poses.length > 0) {
        let kp = poses[0].keypoints;
        stroke(255, 255, 255, 150);
        strokeWeight(2);
        let ls = kp[5],
            rs = kp[6];
        let neck = createVector((ls.x + rs.x) / 2, (ls.y + rs.y) / 2);
        let hip = kp[11].score > kp[12].score ? kp[11] : kp[12];
        let knee = kp[13].score > kp[14].score ? kp[13] : kp[14];
        let ank = kp[15].score > kp[16].score ? kp[15] : kp[16];
        let ear = kp[3].score > kp[4].score ? kp[3] : kp[4];
        if (ear.score > MIN_SCORE) line(ear.x, ear.y, neck.x, neck.y);
        if (hip.score > MIN_SCORE) line(neck.x, neck.y, hip.x, hip.y);
        if (knee.score > MIN_SCORE) line(hip.x, hip.y, knee.x, knee.y);
        if (ank.score > MIN_SCORE) line(knee.x, knee.y, ank.x, ank.y);
        let el = kp[7].score > kp[8].score ? kp[7] : kp[8];
        let sh = el === kp[7] ? kp[5] : kp[6];
        let wr = el === kp[7] ? kp[9] : kp[10];
        if (sh.score > MIN_SCORE) line(sh.x, sh.y, el.x, el.y);
        if (wr.score > MIN_SCORE) line(el.x, el.y, wr.x, wr.y);
        noStroke();
        fill(255, 0, 0);
        for (let pt of kp) if (pt.score > MIN_SCORE) circle(pt.x, pt.y, 8);
        fill(0, 255, 0);
        circle(neck.x, neck.y, 8);
    }
}

function updateDebugTextBox() {
    let lines = [];
    lines.push(`Frame ${sampleCount}/${MAX_SAMPLES}`);
    if (currentMetrics) {
        lines.push(`Ear–Neck–Hip: ${currentMetrics.enh_angle.toFixed(1)}°`);
        lines.push(`Hip–Ankle Slope: ${currentMetrics.ha_slope.toFixed(3)}`);
        lines.push(`Global Angle: ${currentMetrics.global_angle.toFixed(1)}°`);
        lines.push(`Arm Angle: ${currentMetrics.arm_angle.toFixed(1)}°`);
    }
    debugTextBox.value(lines.join("\n"));
}

function drawSummaryPanel() {
    fill(0, 0, 0, 200);
    noStroke();
    rect(0, 530, 640, 70);
    fill(text_color);
    textSize(16);
    text(
        `Ear–Neck–Hip: mean ${hnhStats.mean.toFixed(1)}° ` +
            `(exp ${BENCHMARK.EAR_NECK_HIP.min}–${BENCHMARK.EAR_NECK_HIP.max})`,
        20,
        555
    );
    text(
        `Hip–Ankle Slope: mean ${haStats.mean.toFixed(3)} ` +
            `(exp ${BENCHMARK.HIP_ANKLE_SLOPE.min}–${BENCHMARK.HIP_ANKLE_SLOPE.max})`,
        20,
        575
    );
    text(
        `Global: mean ${gpStats.mean.toFixed(1)}° ` +
            `(exp ${BENCHMARK.GLOBAL_PLANK.min}–${BENCHMARK.GLOBAL_PLANK.max})`,
        20,
        595
    );
    text(
        `Arm: mean ${armStats.mean.toFixed(1)}° ` +
            `(exp ${BENCHMARK.ARM_ANGLE.min}–${BENCHMARK.ARM_ANGLE.max})`,
        350,
        575
    );
}

function toggleCollection() {
    if (!is_detecting) {
        is_detecting = true;
        sampleCount = 0;
        collectionComplete = false;
        hnhStats = { count: 0, mean: 0, M2: 0 };
        haStats = { count: 0, mean: 0, M2: 0 };
        gpStats = { count: 0, mean: 0, M2: 0 };
        armStats = { count: 0, mean: 0, M2: 0 };
        start_button.html("PAUSE COLLECTION");
    } else {
        is_detecting = false;
        start_button.html("RESUME COLLECTION");
    }
}

function addSample(stats, value) {
    stats.count++;
    let delta = value - stats.mean;
    stats.mean += delta / stats.count;
    let delta2 = value - stats.mean;
    stats.M2 += delta * delta2;
}

function measurePlankMetrics(p) {
    let kp = p.keypoints;
    let ear = kp[3].score > kp[4].score ? kp[3] : kp[4];
    let ls = kp[5],
        rs = kp[6];
    let neck = { x: (ls.x + rs.x) / 2, y: (ls.y + rs.y) / 2 };
    let hip = kp[11].score > kp[12].score ? kp[11] : kp[12];
    let ank = kp[15].score > kp[16].score ? kp[15] : kp[16];
    let el = kp[7].score > kp[8].score ? kp[7] : kp[8];
    let sh = el === kp[7] ? kp[5] : kp[6];
    let enh = angleBetween(ear, neck, hip);
    let slope = (ank.y - hip.y) / (ank.x - hip.x);
    let global = angleBetween(ank, hip, ear);
    let wr = el === kp[7] ? kp[9] : kp[10];
    let arm = angleBetween(sh, el, wr);
    return {
        enh_angle: enh,
        ha_slope: slope,
        global_angle: global,
        arm_angle: arm,
    };
}

function angleBetween(a, b, c) {
    let v1 = createVector(a.x - b.x, a.y - b.y);
    let v2 = createVector(c.x - b.x, c.y - b.y);
    let dot = v1.dot(v2);
    let m = v1.mag() * v2.mag();
    if (m === 0) return 0;
    let cosA = constrain(dot / m, -1, 1);
    return degrees(acos(cosA));
}
