const http = require('http');
const fs = require('fs');

const BASE_URL = "http://localhost:5000/api";

function fetch(url, options = {}) {
    return new Promise((resolve, reject) => {
        const req = http.request(url, options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    try {
                        resolve(JSON.parse(data));
                    } catch(e) {
                        resolve(data);
                    }
                } else {
                    reject(new Error(`Status ${res.statusCode}: ${data}`));
                }
            });
        });
        req.on('error', reject);
        if (options.body) {
            req.write(options.body);
        }
        req.end();
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function triggerIncident() {
    console.log("Mocking high CPU usage...");
    fs.writeFileSync("mock_cpu_high.txt", "mock");
}

async function getIncidents() {
    try {
        return await fetch(`${BASE_URL}/incidents`);
    } catch(e) {
        return [];
    }
}

async function waitForIncident(statusFilter, timeoutSeconds) {
    console.log(`Waiting up to ${timeoutSeconds}s for an incident to appear/change...`);
    for (let i = 0; i < timeoutSeconds; i++) {
        const incidents = await getIncidents();
        if (incidents && incidents.length > 0) {
            if (statusFilter) {
                const inc = incidents.find(inc => statusFilter.includes(inc.status) && ["Critical CPU Usage", "Correlated System Degradation"].includes(inc.title));
                if (inc) return inc;
            } else {
                const inc = incidents.find(inc => ["Critical CPU Usage", "Correlated System Degradation"].includes(inc.title));
                if (inc) return inc;
            }
        }
        await sleep(1000);
    }
    return null;
}

async function testPhase2() {
    console.log("--- Phase 2 E2E Test (Detection -> AI RCA -> Remediation -> Verification -> Resolved) ---");
    
    try {
        triggerIncident();
        
        let incident = await waitForIncident(["ACTION_REQUIRED", "REMEDIATING", "VERIFYING", "RESOLVED"], 60);
        
        if (!incident) {
            const active = await waitForIncident(["OPEN", "INVESTIGATING"], 5);
            if (active) {
                console.error(`[FAIL] Incident stuck in ${active.status}. AI analysis probably failed.`);
            } else {
                console.error(`[FAIL] Test failed: Incident was not detected.`);
            }
            process.exit(1);
        }
        
        console.log(`[PASS] Incident ${incident.id} reached status ${incident.status}`);
        const incId = incident.id;
        
        const details = await fetch(`${BASE_URL}/incidents/${incId}`);
        
        if (!details.root_cause) {
            console.log("[WARN] No root cause found. Did AI analysis run?");
        } else {
            console.log(`[PASS] AI Root Cause identified: ${details.root_cause}`);
        }
            
        if (!details.recommendation) {
            console.log("[WARN] No recommendation found.");
        } else {
            console.log(`[PASS] AI Recommendation provided: ${details.recommendation}`);
        }

        const actions = details.actions || [];
        const pendingAction = actions.find(a => ["PENDING", "APPROVED"].includes(a.status));
        
        if (!pendingAction) {
            console.error("[FAIL] No pending or approved actions found for remediation.");
            process.exit(1);
        }
            
        console.log(`[PASS] Found action to execute: ${pendingAction.action_type} (Status: ${pendingAction.status})`);
        
        if (pendingAction.status === "PENDING") {
            console.log(`Approving action ${pendingAction.id}...`);
            await fetch(`${BASE_URL}/incidents/${incId}/actions/${pendingAction.id}/approve`, {method: "POST"});
            console.log("[PASS] Action approved.");
        }
            
        console.log("Simulating that the action fixes the CPU problem by removing mock...");
        if (fs.existsSync("mock_cpu_high.txt")) {
            fs.unlinkSync("mock_cpu_high.txt");
        }
            
        console.log(`Executing action ${pendingAction.id}...`);
        await fetch(`${BASE_URL}/incidents/${incId}/actions/${pendingAction.id}/execute`, {method: "POST"});
        console.log("[PASS] Action executed successfully.");
        
        console.log("Waiting for verification to complete and incident to resolve...");
        let resolved = false;
        let finalInc = null;
        for (let i = 0; i < 20; i++) {
            await sleep(2000);
            finalInc = await fetch(`${BASE_URL}/incidents/${incId}`);
            if (finalInc.status === "RESOLVED") {
                resolved = true;
                break;
            }
        }
                
        if (!resolved) {
            console.error(`[FAIL] Test failed: Incident did not become RESOLVED. Status: ${finalInc.status}`);
            process.exit(1);
        }
            
        console.log(`[PASS] Incident ${incId} verified and RESOLVED!`);
        console.log("\nAll Phase 2 lifecycle tests passed!");
    } catch(e) {
        if (fs.existsSync("mock_cpu_high.txt")) {
            fs.unlinkSync("mock_cpu_high.txt");
        }
        console.error(`[FAIL] Exception during test: ${e}`);
        process.exit(1);
    }
}

testPhase2();
