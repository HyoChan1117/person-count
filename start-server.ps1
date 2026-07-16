# Docker가 준비될 때까지 대기
$timeout = 120
$elapsed = 0
Write-Host "Docker 준비 대기 중..."
while ($elapsed -lt $timeout) {
    try {
        docker info 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
    } catch {}
    Start-Sleep -Seconds 5
    $elapsed += 5
}

# Docker Compose 시작
Set-Location "c:\.code\person-count"
docker-compose up -d
Write-Host "Docker Compose 시작 완료"

# 컨테이너 준비 대기
Start-Sleep -Seconds 10

# ngrok 시작 (최소화)
Start-Process ngrok -ArgumentList "http 80 --domain=approach-plausible-cannot.ngrok-free.dev" -WindowStyle Minimized
Write-Host "ngrok 시작 완료"
