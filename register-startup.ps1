$scriptPath = "c:\.code\person-count\start-server.ps1"
$command = "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`""

Set-ItemProperty `
    -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" `
    -Name "PersonCountServer" `
    -Value $command

Write-Host "시작 프로그램 등록 완료 (로그인 시 자동 실행)"
