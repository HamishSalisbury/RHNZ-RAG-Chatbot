<#
.SYNOPSIS
    Fires POST requests at the /ask endpoint at a target rate to exercise
    DRF throttling (BurstRateThrottle / SustainedRateThrottle).

.DESCRIPTION
    Sends $RatePerSecond requests each second for $DurationSeconds seconds,
    then waits for every request to complete and prints a tally of HTTP
    status codes. Expect a mix of 200 (allowed) and 429 (throttled) once the
    rate limits are exceeded.

.EXAMPLE
    .\load-test-ask.ps1
    .\load-test-ask.ps1 -DurationSeconds 5 -RatePerSecond 100
    .\load-test-ask.ps1 -Url "http://127.0.0.1:8000/v1/ask" -Question "What is the offside rule?"
#>
param(
    [string]$Url             = "http://127.0.0.1:8000/v1/ask/",
    [int]   $RatePerSecond   = 100,
    [int]   $DurationSeconds = 10,
    [string]$Question        = "What is the offside rule?"
)

# HttpClient gives real concurrency; needed to actually reach 100/s.
Add-Type -AssemblyName System.Net.Http

$handler = [System.Net.Http.HttpClientHandler]::new()
$client  = [System.Net.Http.HttpClient]::new($handler)
$client.Timeout = [TimeSpan]::FromSeconds(30)

$bodyJson = @{ question = $Question } | ConvertTo-Json -Compress

$allTasks = [System.Collections.Generic.List[System.Threading.Tasks.Task[System.Net.Http.HttpResponseMessage]]]::new()

Write-Host "Firing $RatePerSecond req/s at $Url for $DurationSeconds s ..." -ForegroundColor Cyan

$overall = [System.Diagnostics.Stopwatch]::StartNew()

for ($sec = 0; $sec -lt $DurationSeconds; $sec++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    for ($i = 0; $i -lt $RatePerSecond; $i++) {
        # A fresh StringContent per request - HttpClient disposes it after send.
        $content = [System.Net.Http.StringContent]::new(
            $bodyJson,
            [System.Text.Encoding]::UTF8,
            "application/json"
        )
        $allTasks.Add($client.PostAsync($Url, $content))
    }

    # Pace the loop so each batch of $RatePerSecond spans ~1 second.
    $remaining = 1000 - $sw.ElapsedMilliseconds
    if ($remaining -gt 0) { Start-Sleep -Milliseconds $remaining }

    Write-Host ("  dispatched second {0}/{1} ({2} requests in flight)" -f ($sec + 1), $DurationSeconds, $allTasks.Count)
}

Write-Host "All requests dispatched; waiting for responses..." -ForegroundColor Cyan
[System.Threading.Tasks.Task]::WaitAll($allTasks.ToArray())
$overall.Stop()

# Tally results by status code.
$counts = @{}
$faults = 0

foreach ($t in $allTasks) {
    if ($t.IsFaulted) {
        $faults++
        continue
    }
    $code = [int]$t.Result.StatusCode
    if ($counts.ContainsKey($code)) { $counts[$code]++ } else { $counts[$code] = 1 }
    $t.Result.Dispose()
}

$total = $allTasks.Count
$elapsed = $overall.Elapsed.TotalSeconds

Write-Host ""
Write-Host "==================== RESULTS ====================" -ForegroundColor Green
Write-Host ("Total requests sent : {0}" -f $total)
Write-Host ("Elapsed             : {0:N2} s" -f $elapsed)
Write-Host ("Effective rate      : {0:N1} req/s" -f ($total / $elapsed))
Write-Host ("Network faults      : {0}" -f $faults)
Write-Host "By HTTP status:"
foreach ($code in ($counts.Keys | Sort-Object)) {
    $label = switch ($code) {
        200 { "OK (allowed)" }
        400 { "Bad Request (missing 'question')" }
        429 { "Too Many Requests (throttled)" }
        503 { "Service Unavailable (index/LLM)" }
        default { "" }
    }
    Write-Host ("  {0}  {1,5}   {2}" -f $code, $counts[$code], $label)
}
Write-Host "=================================================" -ForegroundColor Green

$client.Dispose()
