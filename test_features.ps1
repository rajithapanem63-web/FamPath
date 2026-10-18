
$BASE = "http://localhost:8000/api/v1"
$pass = 0; $fail = 0

function Ok {
    param([string]$label, [bool]$cond, [string]$detail="")
    if ($cond) { Write-Host "  [PASS] $label" }
    else        { Write-Host "  [FAIL] $label  ($detail)" }
    if ($cond) { $script:pass++ } else { $script:fail++ }
}

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 1. AUTH ==="

$lr = Invoke-WebRequest -Method POST -Uri "$BASE/auth/login" `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"email":"famtest_143124@fampath.dev","password":"Test@5678"}' -UseBasicParsing
$lj = $lr.Content | ConvertFrom-Json
$TOKEN = $lj.access_token
$AH = @{"Content-Type"="application/json";"Authorization"="Bearer $TOKEN"}
Ok "Login 200"       ($lr.StatusCode -eq 200)
Ok "Token present"   ($TOKEN.Length -gt 20)
Ok "Role = student"  ($lj.user.role -eq "student")

$me = (Invoke-WebRequest -Uri "$BASE/auth/me" -Headers $AH -UseBasicParsing).Content | ConvertFrom-Json
Ok "GET /me email"   ($me.email -eq "famtest_143124@fampath.dev")

# Auth negatives — catch the exception and read StatusCode from the response
$badR = $null
try { Invoke-WebRequest -Method POST -Uri "$BASE/auth/login" -Headers @{"Content-Type"="application/json"} -Body '{"email":"famtest_143124@fampath.dev","password":"wrong"}' -UseBasicParsing | Out-Null }
catch [System.Net.WebException] { $badR = [int]$_.Exception.Response.StatusCode }
Ok "Wrong password = 401"  ($badR -eq 401)  $badR

$noTok = $null
try { Invoke-WebRequest -Uri "$BASE/auth/me" -UseBasicParsing | Out-Null }
catch [System.Net.WebException] { $noTok = [int]$_.Exception.Response.StatusCode }
Ok "No token = 401"  ($noTok -eq 401)  $noTok

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 2. WORKSPACE ==="

$wsr = Invoke-WebRequest -Uri "$BASE/workspaces" -Headers $AH -UseBasicParsing
$wsj = $wsr.Content | ConvertFrom-Json
# Create workspace if none exist
if ($wsj.Count -eq 0) {
    $newWs = (Invoke-WebRequest -Method POST -Uri "$BASE/workspaces" -Headers $AH -Body '{"name":"Test Family 2025"}' -UseBasicParsing).Content | ConvertFrom-Json
    $WS = $newWs.id
} else {
    $WS = $wsj[0].id
}
Ok "List workspaces 200"  ($wsr.StatusCode -eq 200)
Ok "Workspace ID present" ($WS.Length -gt 10)

$wsd = (Invoke-WebRequest -Uri "$BASE/workspaces/$WS" -Headers $AH -UseBasicParsing).Content | ConvertFrom-Json
Ok "Workspace detail"      ($wsd.id -eq $WS)
Ok "Workspace has members" ($wsd.members.Count -ge 1)

# Profile (PUT to create, then GET)
$profBody = '{"exam_type":"AP_EAPCET","rank":5000,"category":"OC","gender":"male","home_district":"Guntur","home_state":"Andhra Pradesh"}'
$putR = Invoke-WebRequest -Method PUT -Uri "$BASE/profile" -Headers $AH -Body $profBody -UseBasicParsing
Ok "Profile PUT (create/update) 200" ($putR.StatusCode -eq 200)

$getR = Invoke-WebRequest -Uri "$BASE/profile" -Headers $AH -UseBasicParsing
Ok "Profile GET 200"  ($getR.StatusCode -eq 200)
$profJ = $getR.Content | ConvertFrom-Json
Ok "Profile exam_type set" ($profJ.exam_type -eq "AP_EAPCET")

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 3. COLLEGE PREDICTION ==="

$pR = Invoke-WebRequest -Method POST -Uri "$BASE/predict/colleges" -Headers $AH `
    -Body '{"exam_type":"AP_EAPCET","rank":5000,"category":"OC","gender":"male","filters":{"branches":["CSE","ECE"]}}' -UseBasicParsing
$pJ = $pR.Content | ConvertFrom-Json
$CID = $pJ.predictions[0].college_id

Ok "Prediction 200"              ($pR.StatusCode -eq 200)
Ok "Results returned"            ($pJ.predictions.Count -gt 0)  $pJ.predictions.Count
Ok "Safe band present"           (($pJ.predictions | Where-Object band -eq "Safe").Count -gt 0)
Ok "Disclaimer per result"       ($pJ.predictions[0].disclaimer.Length -gt 10)
Ok "SHAP factors present"        ($pJ.predictions[0].shap_factors.Count -gt 0)

$dJ = (Invoke-WebRequest -Method POST -Uri "$BASE/predict/colleges" -Headers $AH `
    -Body '{"exam_type":"AP_EAPCET","rank":120000,"category":"OC","gender":"male"}' -UseBasicParsing).Content | ConvertFrom-Json
Ok "Dream band at rank 120k"     (($dJ.predictions | Where-Object band -eq "Dream").Count -gt 0)

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 4. APTITUDE QUIZ ==="

$qR = Invoke-WebRequest -Uri "$BASE/aptitude/questions" -Headers $AH -UseBasicParsing
$qJ = $qR.Content | ConvertFrom-Json
$SID = $qJ.session_id
Ok "Quiz start 200"          ($qR.StatusCode -eq 200)
Ok "20 questions"            ($qJ.questions.Count -eq 20)

# Build JSON array without -AsArray (PowerShell 5 compat)
$respArr = "[" + (($qJ.questions | ForEach-Object { "{`"question_id`":`"$($_.id)`",`"value`":4}" }) -join ",") + "]"
$sR = Invoke-WebRequest -Method POST -Uri "$BASE/aptitude/sessions/$SID/responses" `
    -Headers $AH -Body "{`"responses`":$respArr}" -UseBasicParsing
$sJ = $sR.Content | ConvertFrom-Json
Ok "Save responses 200"      ($sR.StatusCode -eq 200)
Ok "20 responses tracked"    ($sJ.progress.answered -eq 20)

$subR = Invoke-WebRequest -Method POST -Uri "$BASE/aptitude/sessions/$SID/submit" -Headers $AH -UseBasicParsing
$subJ = $subR.Content | ConvertFrom-Json
Ok "Submit 200"              ($subR.StatusCode -eq 200)
Ok "RIASEC I score > 0"      ($subJ.riasec_scores.I -gt 0)
Ok "Branch recs returned"    ($subJ.top_branches.Count -gt 0)

$latR = Invoke-WebRequest -Uri "$BASE/aptitude/results/latest" -Headers $AH -UseBasicParsing
Ok "Latest result 200"       ($latR.StatusCode -eq 200)

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 5. FAMILY ALIGNMENT ==="

$alR = Invoke-WebRequest -Uri "$BASE/alignment/$WS/dashboard" -Headers $AH -UseBasicParsing
$alJ = $alR.Content | ConvertFrom-Json
Ok "Alignment dashboard 200"   ($alR.StatusCode -eq 200)
Ok "alignment_score key"       ($alJ.PSObject.Properties.Name -contains "alignment_score")

$prefBody = '{"preferences":{"branch_interest":4,"location_flexibility":3,"budget_priority":4,"placement_focus":5,"higher_education":2,"job_stability":4,"startup_openness":3,"prestige_weight":3}}'
$alPR = Invoke-WebRequest -Method POST -Uri "$BASE/alignment/$WS/preferences" `
    -Headers $AH -Body $prefBody -UseBasicParsing
Ok "Submit prefs 200/201"    ($alPR.StatusCode -in @(200,201))

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 6. PREFERENCES ==="

$myP = Invoke-WebRequest -Uri "$BASE/preferences/me?workspace_id=$WS" -Headers $AH -UseBasicParsing
Ok "GET own prefs 200"  ($myP.StatusCode -eq 200)

$famP = Invoke-WebRequest -Uri "$BASE/preferences/family?workspace_id=$WS" -Headers $AH -UseBasicParsing
Ok "GET family summary 200"  ($famP.StatusCode -eq 200)

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 7. COST & ROI ==="

$fakeProg = "00000000-0000-0000-0000-000000000001"
$costR = Invoke-WebRequest -Uri "$BASE/cost/$CID/$fakeProg" -Headers $AH -UseBasicParsing
$costJ = $costR.Content | ConvertFrom-Json
Ok "Cost 200"              ($costR.StatusCode -eq 200)
Ok "Disclaimer present"    ($costJ.disclaimer.Length -gt 10)

$scR = Invoke-WebRequest -Uri "$BASE/cost/scholarships" -Headers $AH -UseBasicParsing
Ok "Scholarships 200"      ($scR.StatusCode -eq 200)

# Budget plan: required fields are planned_budget_4yr + annual_tuition
$budR = Invoke-WebRequest -Method POST -Uri "$BASE/cost/budget-plan" -Headers $AH `
    -Body '{"planned_budget_4yr":500000,"annual_tuition":120000,"annual_hostel":60000}' -UseBasicParsing
$budJ = $budR.Content | ConvertFrom-Json
Ok "Budget plan 200"        ($budR.StatusCode -eq 200)
Ok "funding_gap present"    ($budJ.PSObject.Properties.Name -contains "funding_gap")

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 8. SHORTLIST ==="

# shortlist requires college_id + program_id — use real seed program ID (JNTUH CSE)
$PROG_ID = "3a26a1e5-2d2c-4db7-a2cb-1394dfa469b5"
$slBody = "{`"college_id`":`"$CID`",`"program_id`":`"$PROG_ID`"}"
$slR = Invoke-WebRequest -Method POST -Uri "$BASE/shortlist/$WS" -Headers $AH -Body $slBody -UseBasicParsing
$slJ = $slR.Content | ConvertFrom-Json
$ITEM_ID = $slJ.id
Ok "Add to shortlist 201"   ($slR.StatusCode -in @(200,201))
Ok "Item ID returned"       ($ITEM_ID -ne $null)

$slgR = Invoke-WebRequest -Uri "$BASE/shortlist/$WS" -Headers $AH -UseBasicParsing
$slgArr = $slgR.Content | ConvertFrom-Json
Ok "GET shortlist 200"      ($slgR.StatusCode -eq 200)
Ok "Shortlist has items"    ($slgArr.Count -ge 1)  $slgArr.Count

if ($ITEM_ID) {
    # vote is an integer: 1=yes, 0=neutral, -1=no
    $vR = Invoke-WebRequest -Method POST -Uri "$BASE/shortlist/$WS/$ITEM_ID/vote" `
        -Headers $AH -Body '{"vote":1,"comment":"Great choice"}' -UseBasicParsing
    Ok "Vote 200/201"       ($vR.StatusCode -in @(200,201))
}

$logR = Invoke-WebRequest -Uri "$BASE/shortlist/$WS/log" -Headers $AH -UseBasicParsing
Ok "Decision log 200"       ($logR.StatusCode -eq 200)

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 9. TIMELINE & CHECKLIST ==="

$tlR = Invoke-WebRequest -Uri "$BASE/timeline/$WS" -Headers $AH -UseBasicParsing
# timeline returns array of event objects
Ok "Timeline 200"     ($tlR.StatusCode -eq 200)

$tkR = Invoke-WebRequest -Method POST -Uri "$BASE/timeline/$WS/tasks" -Headers $AH `
    -Body '{"title":"Submit application form","due_date":"2026-11-01T00:00:00Z","category":"application"}' -UseBasicParsing
Ok "Add task 201"     ($tkR.StatusCode -in @(200,201))

$clR = Invoke-WebRequest -Uri "$BASE/checklist/$WS" -Headers $AH -UseBasicParsing
Ok "Checklist 200"    ($clR.StatusCode -eq 200)

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 10. CHATBOT (RAG) ==="

# consent field name is "consented" (bool)
$conR = Invoke-WebRequest -Method POST -Uri "$BASE/workspaces/$WS/consent" `
    -Headers $AH -Body '{"consented":true}' -UseBasicParsing
Ok "Consent 200/201"   ($conR.StatusCode -in @(200,201))

$csR = Invoke-WebRequest -Method POST -Uri "$BASE/chat/sessions" `
    -Headers $AH -Body "{`"workspace_id`":`"$WS`"}" -UseBasicParsing
$csJ = $csR.Content | ConvertFrom-Json
$CHAT_ID = $csJ.session_id
Ok "Create session"    ($csR.StatusCode -in @(200,201))

if ($CHAT_ID) {
    $msgR = Invoke-WebRequest -Method POST -Uri "$BASE/chat/sessions/$CHAT_ID/messages" `
        -Headers $AH -Body '{"content":"What is AP EAPCET?"}' -UseBasicParsing
    $msgJ = $msgR.Content | ConvertFrom-Json
    Ok "Send message 200"       ($msgR.StatusCode -in @(200,201))
    Ok "Response not empty"     ($msgJ.content.Length -gt 10)
    Ok "Citations field"        ($msgJ.PSObject.Properties.Name -contains "citations")

    $histR = Invoke-WebRequest -Uri "$BASE/chat/sessions/$CHAT_ID/messages" -Headers $AH -UseBasicParsing
    Ok "Chat history 200"       ($histR.StatusCode -eq 200)
    Ok "History has messages"   (($histR.Content | ConvertFrom-Json).Count -ge 1)
}

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 11. COLLEGE COMPARE ==="

$cmpBody = '{"items":[{"college_id":"23fc1cd2-315e-40c2-a31f-08699b44bd38"},{"college_id":"45ad57df-897f-44ac-877d-483ecaf663b8"}]}'
$cmpR = Invoke-WebRequest -Method POST -Uri "$BASE/colleges/compare" -Headers $AH -Body $cmpBody -UseBasicParsing
$cmpJ = $cmpR.Content | ConvertFrom-Json
Ok "Compare 200"         ($cmpR.StatusCode -eq 200)
Ok "2 colleges returned" ($cmpJ.colleges.Count -eq 2)
Ok "Disclaimer present"  ($cmpJ.disclaimer.Length -gt 5)
Ok "Insights returned"   ($cmpJ.PSObject.Properties.Name -contains "insights")

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 12. CAREER ROADMAP ==="

$crR = Invoke-WebRequest -Uri "$BASE/career-roadmap/$WS" -Headers $AH -UseBasicParsing
$crJ = $crR.Content | ConvertFrom-Json
Ok "Roadmap GET 200"          ($crR.StatusCode -eq 200)
Ok "available_options key"    ($crJ.PSObject.Properties.Name -contains "available_options")

# POST to /{workspace_id} with branch_code + career_role
$gR = Invoke-WebRequest -Method POST -Uri "$BASE/career-roadmap/$WS" -Headers $AH `
    -Body '{"branch_code":"CSE","career_role":"Full-Stack Web Development","current_semester":3}' -UseBasicParsing
Ok "Set goal 200/201"         ($gR.StatusCode -in @(200,201))

$cr2R = Invoke-WebRequest -Uri "$BASE/career-roadmap/$WS" -Headers $AH -UseBasicParsing
$cr2J = $cr2R.Content | ConvertFrom-Json
Ok "has_goal = true"          ($cr2J.has_goal -eq $true)
Ok "Skills returned"          ($cr2J.skills.Count -gt 0)
Ok "Roadmap stages"           ($cr2J.roadmap.Count -gt 0)

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 13. ADMIN RBAC ==="

$admStat = $null
try { Invoke-WebRequest -Uri "$BASE/admin/colleges" -Headers $AH -UseBasicParsing | Out-Null }
catch [System.Net.WebException] { $admStat = [int]$_.Exception.Response.StatusCode }
Ok "Admin 403 for student"  ($admStat -eq 403)  $admStat

$frStat = $null
try { Invoke-WebRequest -Uri "$BASE/admin/freshness" -Headers $AH -UseBasicParsing | Out-Null }
catch [System.Net.WebException] { $frStat = [int]$_.Exception.Response.StatusCode }
Ok "Freshness 403 for student"  ($frStat -eq 403)  $frStat

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n=== 14. HEALTH ==="

$hJ = (Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing).Content | ConvertFrom-Json
Ok "Health ok"     ($hJ.status -eq "ok")

$rdJ = (Invoke-WebRequest -Uri "http://localhost:8000/ready" -UseBasicParsing).Content | ConvertFrom-Json
Ok "DB ok"         ($rdJ.db -eq "ok")
Ok "Redis ok"      ($rdJ.redis -in @("ok","fallback"))
Ok "ML model"      ($rdJ.ml_model -in @("ok","fallback"))

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n============================================================"
Write-Host "  TOTAL: $($pass+$fail) tests  |  PASSED: $pass  |  FAILED: $fail"
Write-Host "============================================================"
if ($fail -gt 0) { exit 1 } else { exit 0 }
