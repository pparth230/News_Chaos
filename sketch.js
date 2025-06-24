let allNewsData = {}; // This will hold your loaded JSON data
let currentYearHeadlines = []; // Flattened list of all headlines for the target year
const targetYear = "2001"; // The year you want to visualize

// Define fixed colors for your categories
const categoryColors = {
    "Entertainment": "#008585",    // Dark Teal
    "Education": "#39515b",     // Dark Slate Gray
    "Politics": "#476068",      // Darker Slate Gray
    "Technology": "#706e59",    // Dark Olive Green
    "Socio-Cultural": "#fdb913",// Golden Yellow
    "Economy": "#c8dbd4",          // Light Cyan
    "Sports": "#d4c8b3",            // Light Khaki
    "Crime": "#e641b6"             // Bright Pink
};

// --- Flow Field Parameters ---
let numSteps = 200; // Total segments per curve (controls total length/detail of each curve)
let stepSize = 10; // Length of each segment
let flow;
let zoff = 0; // Z-offset for Perlin noise, to animate the flow field

// --- Data-driven curve properties ---
let curveDataPoints = []; // Stores { x, y, headline_object } for EACH headline

// --- Animation State Variables for Progressive Drawing ---
let globalUnfurlingProgress = 0; // Ranges from 0 to numSteps
const unfurlingSpeed = 0.1; // How many segments to unfurl per frame (adjust for speed of growth)

// --- NEW: Custom Month Range Filter ---
const startMonthFilter = 0; // 0 for January
const endMonthFilter = 6;   // 6 for July (so, January to July inclusive)


// --- FlowField Class ---
class FlowField {
    constructor() {
        this.resolution = 15; // pixels per column/row
        this.cols = floor(width / this.resolution);
        this.rows = floor(height / this.resolution);
        this.field = new Array(this.cols);
        for (let i = 0; i < this.cols; i++) {
            this.field[i] = new Array(this.rows);
        }
    }

    init(zOffFactor) {
        let xoff = 0;
        for (let i = 0; i < this.cols; i++) {
            let yoff = 0;
            for (let j = 0; j < this.rows; j++) {
                let angle = map(noise(xoff, yoff, zOffFactor), 0, 1, 0, TWO_PI);
                this.field[i][j] = p5.Vector.fromAngle(angle);
                yoff += 0.1;
            }
            xoff += 0.1;
        }
    }

    lookup(x, y) {
        let column = floor(x / this.resolution);
        let row = floor(y / this.resolution);
        if (column < 0 || column >= this.cols || row < 0 || row >= this.rows) {
            return null; // Return null if outside field
        }
        return this.field[column][row];
    }
}

// --- P5.js Core Functions ---

function preload() {
    allNewsData = loadJSON('news_spline_data_monthly_headlines.json',
        () => { console.log('JSON data loaded successfully!'); },
        (error) => { console.error('Error loading JSON data:', error); }
    );
}

function setup() {
    createCanvas(windowWidth, windowHeight);
    background(0); // Black background
    colorMode(RGB, 255, 255, 255, 1);
    noFill();

    flow = new FlowField();
    
    if (allNewsData[targetYear]) {
        for (let monthNum in allNewsData[targetYear]) {
            currentYearHeadlines = currentYearHeadlines.concat(allNewsData[targetYear][monthNum]);
        }
        console.log(`Found ${currentYearHeadlines.length} headlines for year ${targetYear} initially.`);

        // --- Filter for custom month range ---
        let filteredHeadlines = currentYearHeadlines.filter(headline => {
            let publishDate = new Date(headline.publish_date);
            let month = publishDate.getMonth(0,6); // 0 for January, 6 for July
            return month >= startMonthFilter && month <= endMonthFilter;
        });
        console.log(`Filtered to ${filteredHeadlines.length} headlines for months ${startMonthFilter+1} to ${endMonthFilter+1}.`);

        filteredHeadlines.sort((a, b) => new Date(a.publish_date) - new Date(b.publish_date));

        // --- Prepare curveDataPoints for ALL filtered headlines ---
        filteredHeadlines.forEach(headline => {
            let startX = random(width);
            let startY = random(height);

            curveDataPoints.push({
                x: startX,
                y: startY,
                headline: headline
            });
        });
        console.log(`Prepared ${curveDataPoints.length} curve data points for the visualization.`);
        
        if (curveDataPoints.length === 0) {
            noLoop();
        }

    } else {
        console.error(`Data for year ${targetYear} not found. Please check targetYear or JSON.`);
        noLoop();
    }
}

// Function to draw an individual flow curve up to a certain segment count
function drawCurve(xpos, ypos, headline, maxSegmentsToDraw) {
    let curveColor = categoryColors[headline.category] || '#AAAAAA';
    let sentiment = headline.news_sentiment;

    let alpha;
    let weight;

    // --- SENTIMENT MAPPING LOGIC ---
    if (abs(sentiment) < 0.05) { // Neutral sentiment
        alpha = random(1, 10); // Extremely low alpha
        weight = random(0.1, 0.5); // Very thin
    } else if (sentiment < 0) { // Negative sentiment
        alpha = map(sentiment, -1, -0.05, 80, 200); // Darker opacity
        weight = map(sentiment, -1, -0.05, 0.8, 1.2); // Lesser stroke weight
    } else { // Positive sentiment
        alpha = map(sentiment, 0.05, 1, 150, 255); // Darkest opacity
        weight = map(sentiment, 0.05, 1, 1, 1.8); // Higher stroke weight
    }

    alpha = constrain(alpha, 1, 255);
    weight = constrain(weight, 0.1, 5.0);

    let rc = color(curveColor);
    rc.setAlpha(alpha);
    stroke(rc);
    strokeWeight(weight);

    beginShape();
    curveVertex(xpos, ypos); 
    curveVertex(xpos, ypos);

    for (let i = 0; i < maxSegmentsToDraw; i++) { // Draw segments up to maxSegmentsToDraw
        let pos = flow.lookup(xpos, ypos);
        if (pos) { 
            xpos += pos.x * stepSize;
            ypos += pos.y * stepSize;
        } else {
            break;
        }
        curveVertex(xpos, ypos);
    }
    // Final control point if the curve is fully drawn
    if (maxSegmentsToDraw >= numSteps) {
        curveVertex(xpos, ypos);
    }
    endShape();
}

// draw() runs continuously
function draw() {
    background(0, 10); // Black background with 10 alpha (subtle fade)
    
    // Animate the flow field itself
    zoff += 0.005; 
    flow.init(zoff); 

    // --- Core Animation Logic: All curves unfurl simultaneously ---
    globalUnfurlingProgress += unfurlingSpeed;
    if (globalUnfurlingProgress > numSteps) {
        globalUnfurlingProgress = numSteps; // Cap at 100%
        // Optional: Loop the animation, or stop after one full unfurl cycle
        // globalUnfurlingProgress = 0; // Uncomment to loop the unfurling animation
        // noLoop(); // Uncomment to stop animation after all curves are fully unfurled
    }

    // Draw ALL curves, each unfurling up to the current global progress
    for (let i = 0; i < curveDataPoints.length; i++) {
        let dataPoint = curveDataPoints[i];
        drawCurve(dataPoint.x, dataPoint.y, dataPoint.headline, globalUnfurlingProgress); 
    }
}

// Optional: Adjust canvas size if window is resized
function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
    background(0);
    
    flow = new FlowField(); 
    flow.init(zoff); 
    
    // Reset unfurling progress to start from 0 again on resize
    globalUnfurlingProgress = 0;

    curveDataPoints = [];
    
    // Recalculate filtered headlines for new canvas size
    let filteredHeadlines = currentYearHeadlines.filter(headline => {
        let publishDate = new Date(headline.publish_date);
        let month = publishDate.getMonth();
        return month >= startMonthFilter && month <= endMonthFilter;
    });

    filteredHeadlines.forEach(headline => {
        let startX = random(width);
        let startY = random(height);

        curveDataPoints.push({
            x: startX,
            y: startY,
            headline: headline
        });
    });
    if (curveDataPoints.length > 0) {
        loop();
    } else {
        noLoop();
    }
}