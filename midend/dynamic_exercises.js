let detector,
    video,
    poses = [];
let collecting = false;
let is_going_down = false;
let frame_counter = 0;
let current_rep = null;
let pushup_reps = [];
let rep_feedback = null;
let rep_feedback_time = 0;
let downFrameCount = 0;
let upFrameCount = 0;
const FEEDBACK_DURATION_MS = 1000;

// Countdown variables
let showingCountdown = false;
let countdownStartTime = 0;
const COUNTDOWN_MS = 3000;

let xp_gained = 0;

const dynamicBenchmarks = {
    elbow_down_threshold: 60,
    elbow_up_threshold: 175,
    elbow_delta_min: 75,
    elbow_delta_max: 180,
    chest_disp_min: 60,
    chest_disp_max: 100,
};

const MIN_RIGIDITY_INDEX = 0.1;

function setup() {
    const appContainer = createDiv()
        .id("appContainer")
        .style("width", "100%")
        .style("height", "100vh")
        .style("display", "flex")
        .style("flex-direction", "column")
        .style("align-items", "center")
        .style("justify-content", "center")
        .style("background", "linear-gradient(135deg,#1e293b 0%,#0f172a 100%)")
        .style("padding", "10px")
        .style("box-sizing", "border-box");

    const canvasContainer = createDiv()
        .id("canvasContainer")
        .parent(appContainer)
        .style("position", "relative")
        .style("width", "100%")
        .style("max-width", "640px") // optional cap
        .style("aspect-ratio", "4/3") // keeps it 640×480 shape
        .style("overflow", "hidden")
        .style(
            "box-shadow",
            "0 10px 15px -3px rgba(0,0,0,0.1),0 4px 6px -2px rgba(0,0,0,0.05)"
        );

    const canvas = createCanvas(640, 480).parent(canvasContainer);
    video = createCapture(VIDEO).size(640, 480).hide();

    createElement("h1", "Push-Up Form Tracker")
        .parent(appContainer)
        .style("color", "white")
        .style("font-family", "Arial,sans-serif")
        .style("margin", "0 0 10px 0")
        .style("font-size", "24px")
        .style("width", "100%")
        .style("text-align", "center");

    const statsBar = createDiv()
        .id("statsCounter")
        .parent(canvasContainer)
        .style("position", "absolute")
        .style("top", "2%")
        .style("left", "2%")
        .style(
            "background",
            "linear-gradient(to right,rgba(30,41,59,0.7),rgba(15,23,42,0.7))"
        )
        .style("padding", "8px 15px")
        .style("display", "flex")
        .style("align-items", "center")
        .style("color", "white")
        .style("font-family", "Arial,sans-serif")
        .style("font-size", "14px")
        .style("font-weight", "bold")
        .style("box-shadow", "0 2px 10px rgba(0,0,0,0.2)")
        .style("backdrop-filter", "blur(5px)");
    createSpan("").parent(statsBar);
    const repCounter = createSpan("0")
        .id("repCounter")
        .parent(statsBar)
        .style("color", "#4361ee")
        .style("font-size", "18px")
        .style("margin-right", "5px");
    createSpan(" REPS").parent(statsBar).style("font-size", "14px");

    const btnContainer = createDiv()
        .parent(canvasContainer)
        .style("position", "absolute")
        .style("bottom", "5%")
        .style("left", "50%")
        .style("transform", "translateX(-50%)")
        .style("display", "flex")
        .style("gap", "15px");
    const startBtn = createButton("Start Exercise")
        .id("startStopBtn")
        .parent(btnContainer)
        .style("padding", "10px 20px")
        .style("background", "linear-gradient(45deg, #ff9c00, #ff7b00)")
        .style("color", "#fff")
        .style("font-weight", "bold")
        .style("border", "none")
        .style("cursor", "pointer")
        .style("transition", "all 0.3s ease")
        .style("font-family", "Arial,sans-serif")
        .style("box-shadow", "0 4px 6px rgba(0,0,0,0.1)")
        .style("min-width", "140px")
        .style("text-align", "center")
        .mouseOver(() => {
            startBtn.style("transform", "scale(1.05)");
            startBtn.style("box-shadow", "0 6px 8px rgba(0,0,0,0.2)");
        })
        .mouseOut(() => {
            startBtn.style("transform", "scale(1)");
            startBtn.style("box-shadow", "0 4px 6px rgba(0,0,0,0.1)");
        })
        .mousePressed(toggleSession);
    const resetBtn = createButton("Reset")
        .id("resetBtn")
        .parent(btnContainer)
        .style("padding", "10px 15px")
        .style("background", "linear-gradient(45deg,#64748b,#475569)")
        .style("color", "#fff")
        .style("font-weight", "bold")
        .style("border", "none")
        .style("cursor", "pointer")
        .style("transition", "all 0.3s ease")
        .style("font-family", "Arial,sans-serif")
        .style("box-shadow", "0 4px 6px rgba(0,0,0,0.1)")
        .style("min-width", "80px")
        .style("text-align", "center")
        .mouseOver(() => {
            resetBtn.style("transform", "scale(1.05)");
            resetBtn.style("box-shadow", "0 6px 8px rgba(0,0,0,0.2)");
        })
        .mouseOut(() => {
            resetBtn.style("transform", "scale(1)");
            resetBtn.style("box-shadow", "0 4px 6px rgba(0,0,0,0.1)");
        })
        .mousePressed(() => {
            resetSession();
            updateUIAfterReset();
        });
    const helpBtn = createButton("?")
        .parent(canvasContainer)
        .style("position", "absolute")
        .style("top", "10px")
        .style("right", "10px")
        .style("width", "30px")
        .style("height", "30px")
        .style("background", "rgba(255,255,255,0.2)")
        .style("color", "#fff")
        .style("font-weight", "bold")
        .style("border", "none")
        .style("cursor", "pointer")
        .style("display", "flex")
        .style("justify-content", "center")
        .style("align-items", "center")
        .style("font-size", "18px")
        .mousePressed(showHelpOverlay);

    tf.setBackend("webgl")
        .then(() => tf.ready())
        .then(() =>
            poseDetection.createDetector(
                poseDetection.SupportedModels.MoveNet,
                {
                    modelType:
                        poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING,
                }
            )
        )
        .then((d) => (detector = d));
    noStroke();
    textFont("Arial");
}

function draw() {
    background(0);
    image(video, 0, 0);
    if (!detector) {
        drawLoadingIndicator();
    } else if (collecting) {
        detectPose();
        if (poses.length) drawOverlay();
    }
    drawUI();
    frame_counter++;
}

function drawLoadingIndicator() {
    fill(0, 0, 0, 150);
    rect(0, 0, width, height);
    push();
    translate(width / 2, height / 2);
    noFill();
    strokeWeight(5);
    stroke(67, 97, 238, 150);
    ellipse(0, 0, 60, 60);
    stroke(67, 97, 238);
    arc(0, 0, 60, 60, millis() * 0.005, millis() * 0.005 + PI);
    pop();
    fill(255);
    textSize(16);
    textAlign(CENTER, CENTER);
    text("Loading pose detection...", width / 2, height / 2 + 50);
}

async function detectPose() {
    if (!video.elt || video.elt.readyState < 2) return;
    try {
        const res = await detector.estimatePoses(video.elt);
        poses = res;
        if (poses.length) {
            const m = measurePushupMetrics(poses[0].keypoints);
            detectPushupPhase(m);
        }
    } catch {
        poses = [];
        console.log("Error");
    }
}

function detectPushupPhase(m) {
    const SLACK_DEGREES = 10;

    const downThreshold =
        dynamicBenchmarks.elbow_down_threshold + SLACK_DEGREES;
    const upThreshold = dynamicBenchmarks.elbow_up_threshold - SLACK_DEGREES;

    const MIN_CONSECUTIVE_FRAMES = 2;

    if (!is_going_down) {
        if (m.elbow_angle < downThreshold) {
            downFrameCount++;
            if (downFrameCount >= MIN_CONSECUTIVE_FRAMES) {
                is_going_down = true;
                current_rep = { timestamp_start: Date.now(), down: m };
                downFrameCount = 0;
            }
        } else {
            downFrameCount = 0;
        }
    } else {
        if (m.elbow_angle > upThreshold) {
            upFrameCount++;
            if (upFrameCount >= MIN_CONSECUTIVE_FRAMES) {
                is_going_down = false;
                current_rep.timestamp_end = Date.now();
                current_rep.up = m;
                finalizeRep(current_rep);
                upFrameCount = 0;
            }
        } else {
            upFrameCount = 0;
        }
    }
}

function finalizeRep(r) {
    const b = dynamicBenchmarks;
    const rom = r.up.elbow_angle - r.down.elbow_angle;
    const disp = r.down.chest_y - r.up.chest_y;
    const rigidity = computeRigidity(
        r.down.positions,
        r.up.positions,
        (r.timestamp_end - r.timestamp_start) / 1000
    );
    console.log(rigidity);
    const valid_rep =
        rom >= b.elbow_delta_min &&
        disp >= b.chest_disp_min &&
        rigidity >= MIN_RIGIDITY_INDEX;

    if (valid_rep) {
        pushup_reps.push({
            ...r,
            rom,
            disp,
            rigidity,
            valid_rep,
        });
        xp_gained += 5;
    }

    playSound(valid_rep);

    rep_feedback = valid_rep;
    rep_feedback_time = millis();
    select("#repCounter").html(pushup_reps.length);
    showNotification(
        valid_rep ? "Good Rep!" : "Form Issue",
        valid_rep ? "Perfect form!" : determineFeedback(r, rom, disp, rigidity)
    );
}

function playSound(isGood) {
    const sound = isGood
        ? new Audio("http://localhost:5000/static/good.wav")
        : new Audio("http://localhost:5000/static/bad.wav");
    sound.play().catch((e) => {
        console.error("Error playing sound:", e);
    });
}

function determineFeedback(r, rom, disp, rigidity) {
    const b = dynamicBenchmarks;
    if (rom < b.elbow_delta_min) return "Not going low enough";
    if (disp < b.chest_disp_min) return "Not enough chest movement";
    if (rigidity < MIN_RIGIDITY_INDEX)
        return "Body not rigid enough - keep your back straight";
    return "Improve your form!";
}

function measurePushupMetrics(kp) {
    const choose = (a, b) => (a.score > b.score ? a : b);
    const ls = kp[5],
        rs = kp[6];
    const neck = { x: (ls.x + rs.x) / 2, y: (ls.y + rs.y) / 2 };
    const shoulder = ls.score > rs.score ? ls : rs;
    const elbow = choose(kp[7], kp[8]),
        wrist = choose(kp[9], kp[10]);
    const hip = choose(kp[11], kp[12]),
        knee = choose(kp[13], kp[14]),
        ankle = choose(kp[15], kp[16]);
    return {
        elbow_angle: angleBetween(shoulder, elbow, wrist),
        chest_y: shoulder.y,
        positions: { neck, hip, knee, ankle },
    };
}

function angleBetween(a, b, c) {
    const v1 = createVector(a.x - b.x, a.y - b.y);
    const v2 = createVector(c.x - b.x, c.y - b.y);
    const m = v1.mag() * v2.mag();
    if (!m) return 0;
    return degrees(acos(constrain(v1.dot(v2) / m, -1, 1)));
}

function computeRigidity(d, u, sec) {
    const keys = ["neck", "hip", "knee", "ankle"];
    const vals = keys.map((k) => (d[k].y - u[k].y) / sec);
    const mean = vals.reduce((s, v) => s + v, 0) / vals.length;
    const sd = sqrt(
        vals.reduce((s, v) => s + (v - mean) ** 2, 0) / vals.length
    );
    return constrain(mean ? 1 - sd / abs(mean) : 0, 0, 1);
}

function drawOverlay() {
    if (!poses.length) return;
    const kp = poses[0].keypoints;
    if (kp.length < 17) return;

    const connections = [
        [3, 4],
        [3, 5],
        [4, 6],
        [5, 6],
        [5, 7],
        [6, 8],
        [7, 9],
        [8, 10],
        [5, 11],
        [6, 12],
        [11, 12],
        [11, 13],
        [12, 14],
        [13, 15],
        [14, 16],
    ];

    drawingContext.save();

    drawingContext.shadowOffsetX = 0;
    drawingContext.shadowOffsetY = 0;
    drawingContext.shadowBlur = 10;
    drawingContext.shadowColor = "rgba(67, 97, 238, 0.7)";

    for (const [i1, i2] of connections) {
        const p1 = kp[i1];
        const p2 = kp[i2];

        if (p1.score > 0.5 && p2.score > 0.5) {
            const grad = drawingContext.createLinearGradient(
                p1.x,
                p1.y,
                p2.x,
                p2.y
            );
            grad.addColorStop(0, "rgba(67, 97, 238, 0.8)");
            grad.addColorStop(1, "rgba(114, 9, 183, 0.8)");

            drawingContext.beginPath();
            drawingContext.lineWidth = 3;
            drawingContext.strokeStyle = grad;
            drawingContext.moveTo(p1.x, p1.y);
            drawingContext.lineTo(p2.x, p2.y);
            drawingContext.stroke();
        }
    }

    kp.forEach((pt, i) => {
        if (pt.score > 0.5) {
            let radius = 4;

            if ([5, 6, 7, 8, 11, 12, 13, 14].includes(i)) {
                radius = 6;
            }

            const jointGradient = drawingContext.createRadialGradient(
                pt.x,
                pt.y,
                0,
                pt.x,
                pt.y,
                radius * 2
            );
            jointGradient.addColorStop(0, "rgba(114, 9, 183, 1)");
            jointGradient.addColorStop(1, "rgba(67, 97, 238, 0.5)");

            drawingContext.fillStyle = jointGradient;
            drawingContext.beginPath();
            drawingContext.arc(pt.x, pt.y, radius, 0, 2 * Math.PI);
            drawingContext.fill();
        }
    });

    drawingContext.restore();

    if (is_going_down && collecting) {
        const elbow = choose(kp[7], kp[8]);
        if (elbow.score > 0.5) {
            noFill();
            stroke(255, 255, 0, 150 + 100 * sin(millis() * 0.01));
            strokeWeight(2);
            circle(elbow.x, elbow.y, 20);
        }
    }
}

function drawUI() {
    const total = pushup_reps.length;
    const valid = pushup_reps.filter((r) => r.valid_rep).length;
    const accuracy = total ? ((valid / total) * 100).toFixed(1) : "0.0";

    drawMetricsPanel(total, valid, accuracy);

    drawProgressBar(total, valid);

    drawStatusText(collecting);

    if (pushup_reps.length) {
        drawDetailedMetrics(pushup_reps[pushup_reps.length - 1]);
    }

    if (
        rep_feedback !== null &&
        millis() - rep_feedback_time < FEEDBACK_DURATION_MS
    ) {
        drawFeedbackOverlay(
            rep_feedback,
            (millis() - rep_feedback_time) / FEEDBACK_DURATION_MS
        );
    }

    if (!collecting && total === 0) {
        drawStartPrompt();
    }
}

function drawMetricsPanel(total, valid, accuracy) {
    drawingContext.save();
    drawingContext.shadowOffsetX = 0;
    drawingContext.shadowOffsetY = 4;
    drawingContext.shadowBlur = 8;
    drawingContext.shadowColor = "rgba(0, 0, 0, 0.3)";

    const panelX = width - 220;
    const panelY = 10;
    const panelW = 210;
    const panelH = 120;

    const panelGrad = drawingContext.createLinearGradient(
        panelX,
        panelY,
        panelX + panelW,
        panelY + panelH
    );
    panelGrad.addColorStop(0, "rgba(15, 23, 42, 0.85)");
    panelGrad.addColorStop(1, "rgba(30, 41, 59, 0.85)");
    drawingContext.fillStyle = panelGrad;

    drawingContext.beginPath();
    drawingContext.roundRect(panelX, panelY, panelW, panelH, 10);
    drawingContext.fill();
    drawingContext.restore();

    fill(255);
    textAlign(CENTER, TOP);
    textSize(18);
    textStyle(BOLD);
    text("EXERCISE STATS", panelX + panelW / 2, panelY + 15);

    textAlign(CENTER, CENTER);
    textSize(42);
    textStyle(BOLD);
    fill("#4361ee");
    text(total, panelX + panelW / 2, panelY + 60);

    textSize(14);
    fill(200);
    textStyle(NORMAL);
    text("REPS", panelX + panelW / 2, panelY + 85);

    textAlign(RIGHT, CENTER);
    textSize(16);
    if (accuracy >= 80) fill("#4ade80");
    else if (accuracy >= 60) fill("#fb923c");
    else fill("#f87171");

    text(`${accuracy}%`, panelX + panelW - 20, panelY + 105);
    textAlign(LEFT, CENTER);
    fill(200);
    text("Accuracy", panelX + 20, panelY + 105);
}

function drawProgressBar(total, valid) {
    const barY = height - 30;
    const barH = 6;
    noStroke();
    fill(255, 255, 255, 30);
    rect(0, barY, width, barH, barH / 2);

    if (total > 0) {
        const progressWidth = (valid / max(total, 1)) * width;

        const barGrad = drawingContext.createLinearGradient(
            0,
            barY,
            width,
            barY
        );
        barGrad.addColorStop(0, "#4361ee");
        barGrad.addColorStop(1, "#7209b7");
        drawingContext.fillStyle = barGrad;

        rect(0, barY, progressWidth, barH, barH / 2);

        drawingContext.save();
        drawingContext.shadowOffsetX = 0;
        drawingContext.shadowOffsetY = 0;
        drawingContext.shadowBlur = 8;
        drawingContext.shadowColor = "#4361ee";
        rect(0, barY, progressWidth, barH, barH / 2);
        drawingContext.restore();
    }
}

function drawDetailedMetrics(lastRep) {
    drawingContext.save();
    drawingContext.shadowOffsetX = 0;
    drawingContext.shadowOffsetY = 4;
    drawingContext.shadowBlur = 8;
    drawingContext.shadowColor = "rgba(0, 0, 0, 0.3)";

    const panelX = 10;
    const panelY = 10;
    const panelW = 180;
    const panelH = 110;

    const panelGrad = drawingContext.createLinearGradient(
        panelX,
        panelY,
        panelX + panelW,
        panelY + panelH
    );
    panelGrad.addColorStop(0, "rgba(30, 41, 59, 0.85)");
    panelGrad.addColorStop(1, "rgba(15, 23, 42, 0.85)");
    drawingContext.fillStyle = panelGrad;

    drawingContext.beginPath();
    drawingContext.roundRect(panelX, panelY, panelW, panelH, 10);
    drawingContext.fill();
    drawingContext.restore();

    fill(255);
    textAlign(LEFT, TOP);
    textSize(14);
    textStyle(BOLD);
    text("FORM METRICS", panelX + 12, panelY + 12);

    textSize(13);
    textStyle(NORMAL);

    const rigidity = lastRep.rigidity.toFixed(2);
    const rigScore = map(lastRep.rigidity, 0, MIN_RIGIDITY_INDEX * 1.2, 0, 1);
    const rigColor = lerpColor(
        color(247, 113, 113),
        color(74, 222, 128),
        constrain(rigScore, 0, 1)
    );

    fill(200);
    text("Rigidity:", panelX + 12, panelY + 70);
    fill(rigColor);
    text(`${rigidity}`, panelX + 90, panelY + 70);

    noStroke();
    fill(255, 255, 255, 30);
    rect(panelX + 12, panelY + 85, 156, 4, 2);
    fill(rigColor);
    rect(panelX + 12, panelY + 85, 156 * constrain(rigScore, 0, 1), 4, 2);
}

function drawFeedbackOverlay(isGood, progress) {
    let alpha = 255;
    if (progress < 0.2) alpha = (progress / 0.2) * 255;
    else if (progress > 0.8) alpha = ((1 - progress) / 0.2) * 255;

    fill(0, 0, 0, 100);
    rect(0, 0, width, height);

    textAlign(CENTER, CENTER);

    const scaleValue = 1 + sin(progress * PI) * 0.1;

    push();
    translate(width / 2, height / 2);
    scale(scaleValue);

    if (isGood) {
        fill(74, 222, 128, alpha);
        textSize(60);
        text("✓", 0, -40);
        textSize(32);
        text("GOOD FORM", 0, 20);
    } else {
        fill(247, 113, 113, alpha);
        textSize(60);
        text("✗", 0, -40);
        textSize(32);
        text("CHECK FORM", 0, 20);
    }
    pop();
}

function drawStatusText(isCollecting) {
    fill(255);
    textAlign(CENTER, BOTTOM);
    textSize(16);

    if (isCollecting) {
        const blink = sin(millis() * 0.005) > 0;
        if (blink) fill(247, 113, 113);
        text("● RECORDING", width / 2, height - 40);
    }
}

function drawStartPrompt() {
    fill(0, 0, 0, 150);
    rect(0, 0, width, height);

    textAlign(CENTER, CENTER);
    textSize(24);
    fill(255);
    text("Get in position and", width / 2, height / 2 - 30);
    text("press Start Exercise", width / 2, height / 2 + 10);
}

function toggleSession() {
    collecting = !collecting;
    const btn = select("#startStopBtn");
    if (btn) {
        if (collecting) {
            btn.html("Stop Exercise");
            btn.style("background", "linear-gradient(45deg, #ef476f, #d90429)");
        } else {
            btn.html("Start Exercise");
            btn.style("background", "linear-gradient(45deg, #ff9c00, #ff7b00)");
        }
    }
}

function resetSession() {
    collecting = false;
    is_going_down = false;
    frame_counter = 0;
    current_rep = null;
    pushup_reps = [];
    rep_feedback = null;
    rep_feedback_time = 0;
    select("#repCounter").html("0");
}

function updateUIAfterReset() {
    const btn = select("#startStopBtn");
    if (btn) {
        btn.html("Start Exercise");
        btn.style("background", "linear-gradient(45deg, #4361ee, #3a0ca3)");
    }

    rep_feedback = null;

    rep_feedback = null;
    rep_feedback_time = millis();

    showNotification("Exercise Reset", "Ready to start again!");
}

function showHelpOverlay() {
    const overlay = createDiv();
    overlay.id("helpOverlay");
    overlay.style("position", "fixed");
    overlay.style("top", "0");
    overlay.style("left", "0");
    overlay.style("width", "100%");
    overlay.style("height", "100%");
    overlay.style("background", "rgba(15, 23, 42, 0.9)");
    overlay.style("display", "flex");
    overlay.style("flex-direction", "column");
    overlay.style("justify-content", "center");
    overlay.style("align-items", "center");
    overlay.style("z-index", "1000");
    overlay.style("backdrop-filter", "blur(5px)");

    const helpBox = createDiv();
    helpBox.parent(overlay);
    helpBox.style("width", "80%");
    helpBox.style("max-width", "500px");
    helpBox.style("background", "rgba(30, 41, 59, 0.95)");
    helpBox.style("padding", "20px");
    helpBox.style("box-shadow", "0 10px 25px rgba(0, 0, 0, 0.2)");

    const helpTitle = createElement("h2", "How to Use Push-Up Form Tracker");
    helpTitle.parent(helpBox);
    helpTitle.style("color", "white");
    helpTitle.style("margin-top", "0");
    helpTitle.style("font-family", "Arial, sans-serif");

    const helpContent = createDiv();
    helpContent.parent(helpBox);
    helpContent.html(`
        <p style="color: white; line-height: 1.6;">
            1. Position yourself in push-up position facing the camera<br>
            2. Click "Start Exercise" to begin tracking<br>
            3. Perform push-ups with good form<br>
            4. The tracker will count reps and evaluate your form<br><br>
            
            <b>Form Metrics:</b><br>
            • <b>Rigidity:</b> Measures how uniform your movement is (higher is better)<br><br>
            
            <b>Tips for Good Form:</b><br>
            • Keep your back straight<br>
            • Lower chest close to the ground<br>
            • Maintain even pace<br>
            • Fully extend arms at the top
        </p>
    `);

    const closeBtn = createButton("Got it");
    closeBtn.parent(helpBox);
    closeBtn.style("background", "linear-gradient(45deg, #4361ee, #3a0ca3)");
    closeBtn.style("color", "white");
    closeBtn.style("border", "none");
    closeBtn.style("padding", "10px 20px");
    closeBtn.style("cursor", "pointer");
    closeBtn.style("font-weight", "bold");
    closeBtn.style("margin-top", "15px");
    closeBtn.style("display", "block");
    closeBtn.style("width", "120px");
    closeBtn.style("margin", "15px auto 0");
    closeBtn.mousePressed(() => {
        overlay.remove();
    });
}

function showNotification(title, message) {
    const notification = createDiv();
    notification.style("position", "absolute");
    notification.style("top", "60px");
    notification.style("left", "50%");
    notification.style("transform", "translateX(-50%)");
    notification.style(
        "background",
        "linear-gradient(45deg, #4361ee, #3a0ca3)"
    );
    notification.style("color", "white");
    notification.style("padding", "10px 20px");
    notification.style("font-family", "Arial, sans-serif");
    notification.style("box-shadow", "0 4px 12px rgba(0, 0, 0, 0.15)");
    notification.style("z-index", "1000");
    notification.style("text-align", "center");
    notification.parent(select("#canvasContainer"));

    const notifTitle = createElement("h3", title);
    notifTitle.parent(notification);
    notifTitle.style("margin", "0 0 5px 0");
    notifTitle.style("font-size", "16px");

    const notifMsg = createElement("p", message);
    notifMsg.parent(notification);
    notifMsg.style("margin", "0");
    notifMsg.style("font-size", "14px");

    setTimeout(() => {
        let opacity = 1;
        const fadeInterval = setInterval(() => {
            opacity -= 0.05;
            notification.style("opacity", opacity);
            if (opacity <= 0) {
                clearInterval(fadeInterval);
                notification.remove();
            }
        }, 20);
    }, 2000);
}

function choose(a, b) {
    return a.score > b.score ? a : b;
}
