# CSV 내부 줄바꿈을 제거해서 LOAD DATA가 안전하게 읽을 수 있는 파일로 변환
# PowerShell Import-Csv 는 RFC 4180(따옴표 안의 줄바꿈 허용)을 올바르게 파싱한다.

$src  = "c:\workspaces\skn28-3RD-2TEAM\csv"
$dest = "c:\workspaces\skn28-3RD-2TEAM\csv\_clean"

New-Item -ItemType Directory -Force -Path $dest | Out-Null

$files = @(
    "people_clean.csv",
    "courses_clean.csv",
    "admissions_clean.csv",
    "events_clean.csv",
    "assets_clean.csv",
    "attachments_clean.csv",
    "course_track_map.csv",
    "rag_documents.csv",
    "rag_chunks.csv",
    "quality_report.csv"
)

foreach ($file in $files) {
    $srcPath  = Join-Path $src $file
    $destPath = Join-Path $dest $file

    # Import-Csv 로 올바르게 파싱 (따옴표 안의 줄바꿈 처리됨)
    $rows = Import-Csv -Path $srcPath -Encoding UTF8

    # 모든 필드의 내부 줄바꿈을 공백으로 치환
    $rows | ForEach-Object {
        $row = $_
        foreach ($prop in $row.PSObject.Properties) {
            $prop.Value = $prop.Value -replace "`r`n", " " -replace "`n", " " -replace "`r", " "
        }
        $row
    } | Export-Csv -Path $destPath -Encoding UTF8 -NoTypeInformation

    $count = ($rows | Measure-Object).Count
    Write-Host "$file : $count rows -> $destPath"
}

Write-Host "완료"
