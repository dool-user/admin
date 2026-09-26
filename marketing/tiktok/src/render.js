const { chromium } = require('playwright'); const fs=require('fs');
(async () => {
  const [html, outDir, dur] = [process.argv[2], process.argv[3], Number(process.argv[4]||18)];
  fs.rmSync(outDir,{recursive:true,force:true}); fs.mkdirSync(outDir,{recursive:true});
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + html); await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(1000);
  const fps=30, n=Math.round(dur*fps);
  for (let i=0;i<n;i++){ await p.evaluate(t=>render(t), i/fps); await p.screenshot({ path:`${outDir}/f${String(i).padStart(4,'0')}.jpg`, type:'jpeg', quality:95 }); }
  console.log('frames',n); await b.close();
})();
