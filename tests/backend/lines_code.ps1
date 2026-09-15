# Count the lines of source code in this repo.
#
# WHY THE REWRITE. The first version took minutes and looked hung:
#
#   1. Get-ChildItem -Recurse walked EVERYTHING first -- .venv,
#      node_modules, .git -- and only then filtered them out. Those
#      three hold tens of thousands of files between them, so almost
#      all the work was spent listing files that were about to be
#      thrown away. Pruning has to happen DURING the walk, not after.
#
#   2. Get-Content | Measure-Object -Line pushes every line of every
#      file through the PowerShell pipeline one object at a time.
#      [System.IO.File]::ReadAllLines reads the file in one go.
#
# Run from the repo root:  powershell -File tests\backend\lines_code.txt

$ErrorActionPreference = 'Stop'

$SkipDirs = @('.git', '.venv', 'node_modules', '__pycache__', 'dist', 'build',
              '.expo', '.next', 'coverage', 'android', 'ios')

$Extensions = @('.py', '.ts', '.tsx', '.js', '.jsx', '.html', '.css', '.scss')

# An explicit stack rather than recursion: it prunes a directory before
# descending, which is the whole point, and it cannot blow the call
# stack on a deep tree.
$stack = [System.Collections.Generic.Stack[string]]::new()
$stack.Push((Get-Location).Path)

$files = [System.Collections.Generic.List[string]]::new()

while ($stack.Count -gt 0) {
    $dir = $stack.Pop()

    foreach ($sub in [System.IO.Directory]::EnumerateDirectories($dir)) {
        $name = [System.IO.Path]::GetFileName($sub)
        if ($SkipDirs -notcontains $name) { $stack.Push($sub) }
    }

    foreach ($file in [System.IO.Directory]::EnumerateFiles($dir)) {
        if ($Extensions -contains [System.IO.Path]::GetExtension($file)) {
            $files.Add($file)
        }
    }
}

$byExtension = @{}
$total = 0

foreach ($file in $files) {
    # ReadAllLines, not Get-Content: one read, no pipeline.
    $count = [System.IO.File]::ReadAllLines($file).Length
    $total += $count

    $ext = [System.IO.Path]::GetExtension($file)
    $byExtension[$ext] = [int]$byExtension[$ext] + $count
}

""
"{0,-10} {1,10} {2,8}" -f 'EXTENSION', 'LINES', 'FILES'
"{0,-10} {1,10} {2,8}" -f ('-' * 9), ('-' * 10), ('-' * 8)

foreach ($ext in ($byExtension.Keys | Sort-Object { -$byExtension[$_] })) {
    $fileCount = ($files | Where-Object { [System.IO.Path]::GetExtension($_) -eq $ext }).Count
    "{0,-10} {1,10:N0} {2,8:N0}" -f $ext, $byExtension[$ext], $fileCount
}

""
"{0,-10} {1,10:N0} {2,8:N0}" -f 'TOTAL', $total, $files.Count
""
