# Plan: Fix Dragon Demo in index.html

## Problem
- The fsWrite tool and readFile tool were returning stale/cached content
- Dragon demo was added INSIDE the panda screen instead of as a SEPARATE section
- Dragon emoji 🐉 was not rendering properly

## Solution
Use PowerShell to directly write the file content to ensure changes apply.

## Key Requirements from test-dragon.html:
1. Dragon demo must be a SEPARATE section AFTER panda demo
2. CSS for dragon-wrap: `right: -250px` (start position)
3. CSS for dragon: `font-size: 60px`
4. Dragon banner text: "📅 Meeting with James happening at 4:30PM Today"
5. Animation: slide in → show banner → hide banner → slide out to 120%

## File to modify:
`C:\Project1\hit_and_run_pet\website\index.html`

## Structure needed:
```html
<section class="demo" id="demo">
    <!-- Panda demo here -->
</section>

<section class="demo2">
    <p class="demo-label">Meeting reminders</p>
    <div class="screen-wrap">
        <div class="demo2-screen">
            <div class="dragon-wrap" id="dragonWrap">
                <div class="dragon-banner" id="dragonBanner">📅 Meeting with James happening at 4:30PM Today</div>
                <div class="dragon">🐉</div>
            </div>
        </div>
    </div>
</section>

<section class="features">
    <!-- Features here -->
</section>
```

## Verification
After changes, run:
```powershell
Select-String -Path "hit_and_run_pet\website\index.html" -Pattern "demo2-screen|🐉" -Context 2,2
```
