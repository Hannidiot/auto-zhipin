<#
.SYNOPSIS
    Executes multiple job queries and saves results to timestamped JSON files.
.DESCRIPTION
    Runs the query.py script for each provided query, saving output to files named jobs_{query}_{timestamp}.json
.PARAMETER Queries
    Array of job query strings to search for
.PARAMETER City
    BOSS city code (default: 101020100)
.PARAMETER Salary
    BOSS salary code (default: 406)
.PARAMETER ScrollN
    Number of scrolls (default: 8)
.EXAMPLE
    .\run_queries.ps1 -Queries ".net","java","python"
#>

param(
    [Parameter(Mandatory=$true)]
    [string[]]$Queries,
    
    [string]$City = "101020100",
    [string]$Salary = "406",
    [int]$ScrollN = 8
)

foreach ($query in $Queries) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputFile = "jobs_$($query)_$($timestamp).json"
    
    Write-Host "Running query for: $query"
    uv run query.py -q $query --city $City -n $ScrollN --salary $Salary --output $outputFile
    
    if (Test-Path $outputFile) {
        Write-Host "Results saved to: $outputFile"
    } else {
        Write-Warning "No results found for query: $query"
    }
}

Write-Host "All queries completed"
