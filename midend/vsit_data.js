let detector;
let video;
let poses = [];

let isDetecting = false;
let startButton;
let debugTextBox;
let font;

const MAX_SAMPLES = 1000;
let sampleCount = 0;

// Three Welford stats objects
let hnhStats = { count: 0, mean: 0, M2: 0 };
let nhkStats = { count: 0, mean: 0, M2: 0 };
let hkaStats = { count: 0, mean: 0, M2: 0 };

let currentMetrics = null;
let collectionComplete = false;
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

    startButton = createButton("START COLLECTION");
    startButton.position(10, 10);
    startButton.size(200, 50);
    startButton.style("background-color", "#2980b9");
    startButton.style("color", "white");
    startButton.style("border", "none");
    startButton.style("border-radius", "25px");
    startButton.style("font-size", "18px");
    startButton.style("font-weight", "bold");
    startButton.style("cursor", "pointer");
    startButton.mousePressed(toggleCollection);

    debugTextBox = createElement("textarea");
    debugTextBox.attribute("rows", "6");
    debugTextBox.attribute("cols", "80");
    debugTextBox.position(10, 500);

    textFont(font);
}

function draw() {
    background(0);
    image(video, 0, 0);

    if (detector && isDetecting && sampleCount < MAX_SAMPLES) {
        detectPose();
    }

    drawOverlay();
    updateDebugTextBox();

    if (collectionComplete) {
        drawSummaryPanel();
    }
}

async function detectPose() {
    // guard against zero-size texture
    if (!video.elt.videoWidth || !video.elt.videoHeight) return;
    const est = await detector.estimatePoses(video.elt);
    poses = est;
    if (poses.length > 0 && !collectionComplete) {
        let m = measureAngles(poses[0]);
        currentMetrics = m;
        addSample(hnhStats, m.hnh); // head–neck–hip
        addSample(nhkStats, m.nhk); // neck–hip–knee
        addSample(hkaStats, m.hka); // hip–knee–ankle
        sampleCount++;
        if (sampleCount >= MAX_SAMPLES) {
            collectionComplete = true;
            isDetecting = false;
            startButton.html("RESUME");
        }
    }
}

function drawOverlay() {
    if (!poses.length) return;
    let kp = poses[0].keypoints;
    stroke(255, 255, 255, 150);
    strokeWeight(2);

    // choose best side for ears, hips, knees, ankles
    let ear = choose(kp[3], kp[4]);
    let ls = kp[5],
        rs = kp[6];
    let neck = createVector((ls.x + rs.x) / 2, (ls.y + rs.y) / 2);
    let hip = choose(kp[11], kp[12]);
    let knee = choose(kp[13], kp[14]);
    let ank = choose(kp[15], kp[16]);

    // skeleton: ear→neck→hip→knee→ankle
    if (ear.score > MIN_SCORE) line(ear.x, ear.y, neck.x, neck.y);
    if (hip.score > MIN_SCORE) line(neck.x, neck.y, hip.x, hip.y);
    if (knee.score > MIN_SCORE) line(hip.x, hip.y, knee.x, knee.y);
    if (ank.score > MIN_SCORE) line(knee.x, knee.y, ank.x, ank.y);

    // draw joints
    noStroke();
    fill(255, 0, 0);
    for (let p of [ear, hip, knee, ank]) {
        let x = p.x,
            y = p.y,
            s = p.score;
        if (s > MIN_SCORE) circle(x, y, 8);
    }
    fill(0, 255, 0);
    circle(neck.x, neck.y, 8);
}

function updateDebugTextBox() {
    let lines = [];
    lines.push(`Frame ${sampleCount}/${MAX_SAMPLES}`);
    if (currentMetrics) {
        lines.push(`Head–Neck–Hip:      ${currentMetrics.hnh.toFixed(1)}°`);
        lines.push(`Neck–Hip–Knee:      ${currentMetrics.nhk.toFixed(1)}°`);
        lines.push(`Hip–Knee–Ankle:     ${currentMetrics.hka.toFixed(1)}°`);
    }
    debugTextBox.value(lines.join("\n"));
}

function drawSummaryPanel() {
    fill(0, 0, 0, 200);
    noStroke();
    rect(0, 530, width, 70);

    fill(255);
    textSize(16);
    text(`Head–Neck–Hip mean: ${hnhStats.mean.toFixed(1)}°`, 10, 555);
    text(`Neck–Hip–Knee mean: ${nhkStats.mean.toFixed(1)}°`, 10, 575);
    text(`Hip–Knee–Ankle mean: ${hkaStats.mean.toFixed(1)}°`, 350, 575);
}

function toggleCollection() {
    if (!isDetecting) {
        isDetecting = true;
        sampleCount = 0;
        collectionComplete = false;
        [hnhStats, nhkStats, hkaStats].forEach((s) => {
            s.count = 0;
            s.mean = 0;
            s.M2 = 0;
        });
        startButton.html("PAUSE");
    } else {
        isDetecting = false;
        startButton.html("RESUME");
    }
}

function addSample(stats, value) {
    stats.count++;
    let delta = value - stats.mean;
    stats.mean += delta / stats.count;
    let delta2 = value - stats.mean;
    stats.M2 += delta * delta2;
}

function measureAngles(p) {
    let kp = p.keypoints;
    let ear = choose(kp[3], kp[4]);
    let ls = kp[5],
        rs = kp[6];
    let neck = { x: (ls.x + rs.x) / 2, y: (ls.y + rs.y) / 2 };
    let hip = choose(kp[11], kp[12]);
    let knee = choose(kp[13], kp[14]);
    let ank = choose(kp[15], kp[16]);

    let hnh = angleBetween(ear, neck, hip);
    let nhk = angleBetween(neck, hip, knee);
    let hka = angleBetween(hip, knee, ank);

    return { hnh, nhk, hka };
}

function angleBetween(a, b, c) {
    let v1 = createVector(a.x - b.x, a.y - b.y);
    let v2 = createVector(c.x - b.x, c.y - b.y);
    let m = v1.mag() * v2.mag();
    if (m === 0) return 0;
    let cosA = constrain(v1.dot(v2) / m, -1, 1);
    return degrees(acos(cosA));
}

function choose(a, b) {
    return a.score > b.score ? a : b;
}
