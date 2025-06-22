// Push-Up Data Collection System
let detector, video, poses = [];
let collecting = false;
let pushupReps = [];
let currentRep = null;
let isGoingDown = false;
let frameCounter = 0;

function setup() {
    createCanvas(640, 480);
    video = createCapture(VIDEO);
    video.size(640, 480);
    video.hide();
    tf.ready().then(() => {
        poseDetection.createDetector(poseDetection.SupportedModels.MoveNet, {
            modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING
        }).then((d) => detector = d);
    });
    let btn = createButton("Start Push-Up Collection");
    btn.position(10, 10);
    btn.mousePressed(() => collecting = !collecting);
}

function draw() {
    background(0);
    image(video, 0, 0);
    if (collecting && detector) detectPose();
    drawOverlay();
    if (pushupReps.length >= 30) noLoop(), createDownloadButton();
    frameCounter++;
}

async function detectPose() {
    const est = await detector.estimatePoses(video.elt);
    poses = est;
    if (poses.length > 0) {
        const m = measurePushupMetrics(poses[0].keypoints);
        detectPushupPhase(m);
    }
}

function detectPushupPhase(metrics) {
    const elbow = metrics.elbow_angle;
    if (elbow < 70 && !isGoingDown) {
        isGoingDown = true;
        currentRep = {
            timestamp_start: Date.now(),
            down: {
                frame: frameCounter,
                ...metrics
            }
        };
    } else if (elbow > 150 && isGoingDown) {
        currentRep.timestamp_end = Date.now();
        currentRep.up = {
            frame: frameCounter,
            ...metrics
        };
        finalizeRep(currentRep);
        isGoingDown = false;
    }
}

function finalizeRep(rep) {
    const r = rep;
    const range = {
        elbow_delta: r.up.elbow_angle - r.down.elbow_angle,
        shoulder_delta: r.up.shoulder_angle - r.down.shoulder_angle,
        hip_delta: r.up.hip_angle - r.down.hip_angle,
        chest_displacement: r.down.chest_y - r.up.chest_y
    };
    const duration = (r.timestamp_end - r.timestamp_start) / 1000;
    rep.range_of_motion = range;
    rep.duration_sec = duration;
    rep.valid_rep = range.elbow_delta >= 60 && range.chest_displacement >= 20;
    rep.rep_number = pushupReps.length + 1;
    pushupReps.push(rep);
}

function measurePushupMetrics(kp) {
    const shoulder = choose(kp[5], kp[6]);
    const elbow = choose(kp[7], kp[8]);
    const wrist = choose(kp[9], kp[10]);
    const hip = choose(kp[11], kp[12]);
    const knee = choose(kp[13], kp[14]);
    return {
        elbow_angle: angleBetween(shoulder, elbow, wrist),
        shoulder_angle: angleBetween(elbow, shoulder, hip),
        hip_angle: angleBetween(shoulder, hip, knee),
        trunk_slope: (hip.y - shoulder.y) / (hip.x - shoulder.x),
        chest_y: shoulder.y,
        hip_y: hip.y
    };
}

function choose(a, b) {
    return a.score > b.score ? a : b;
}

function angleBetween(a, b, c) {
    const v1 = createVector(a.x - b.x, a.y - b.y);
    const v2 = createVector(c.x - b.x, c.y - b.y);
    const m = v1.mag() * v2.mag();
    if (m === 0) return 0;
    return degrees(acos(constrain(v1.dot(v2) / m, -1, 1)));
}

function drawOverlay() {
    if (!poses.length) return;
    const kp = poses[0].keypoints;
    noFill();
    stroke(0, 255, 0);
    strokeWeight(2);
    for (let pt of kp) {
        if (pt.score > 0.5) circle(pt.x, pt.y, 6);
    }
}

function createDownloadButton() {
    const btn = createButton("Download Push-Up Data");
    btn.position(10, 40);
    btn.mousePressed(() => {
        const data = {
            user_id: "subject_" + Math.floor(Math.random() * 10000),
            timestamp: new Date().toISOString(),
            total_reps: pushupReps.length,
            reps: pushupReps
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: "application/json"
        });
        const url = URL.createObjectURL(blob);
        const a = createA(url, "download.json");
        a.attribute("download", "pushup_data.json");
        a.html("Click here to download");
        a.position(10, 70);
    });
}
