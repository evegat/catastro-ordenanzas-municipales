param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
$python = (Get-Command python -ErrorAction Stop).Source
& $python (Join-Path $PSScriptRoot 'harness.py') @Args
exit $LASTEXITCODE
