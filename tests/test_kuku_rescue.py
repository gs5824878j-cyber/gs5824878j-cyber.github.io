"""Rescue export on the old shared origin. Uses synthetic storage only.
Run beside the kuku-sodate checkout: python3 -m unittest discover -s tests -v
Requires Python Playwright and /usr/bin/chromium.
"""
import asyncio,json,tempfile,unittest,re
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT.parent/'kuku-sodate'
KEY='kuku_preview_v5'
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
class KukuRescueTest(unittest.TestCase):
    def test_same_origin_read_only_allowlisted_export(self):
        self.assertTrue((APP/'app.js').is_file(),'kuku-sodate checkout is required')
        with tempfile.TemporaryDirectory() as tmp:
            doc=Path(tmp)
            (doc/'kuku-sodate').symlink_to(APP,target_is_directory=True)
            (doc/'foremira-data-migration').symlink_to(ROOT/'foremira-data-migration',target_is_directory=True)
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(doc)))
            Thread(target=server.serve_forever,daemon=True).start()
            try: asyncio.run(self.exercise('http://127.0.0.1:'+str(server.server_port),doc))
            finally: server.shutdown();server.server_close()
    async def exercise(self,url,temp):
        async with async_playwright() as p:
            browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            try:
                for variant in ['current','legacy','learned','balanced','pending','empty','corrupt','unknown-field','invalid-score','invalid-date','invalid-pending']:
                    context=await browser.new_context(accept_downloads=True);page=await context.new_page();outbound=[];errors=[]
                    page.on('pageerror',lambda e:errors.append(str(e)))
                    async def route(r):
                        if r.request.url.startswith(url):await r.continue_()
                        else:outbound.append(r.request.url);await r.abort()
                    await context.route('**/*',route)
                    await page.goto(url+'/kuku-sodate/',wait_until='networkidle')
                    if variant=='current':
                        raw=await page.evaluate("() => {S.coins=123;S.pet.xp=160;S.f['2x3'].l=2;save();return localStorage.getItem('kuku_preview_v5')}")
                    elif variant=='legacy': raw=await page.evaluate('JSON.stringify(D())')
                    elif variant=='learned':
                        await page.get_by_role('button',name='📘 新しい段をおぼえる',exact=True).click()
                        await page.get_by_role('button',name='2の段',exact=True).click()
                        await page.get_by_role('button',name='覚えた！ 答えをかくす',exact=True).click()
                        for i in range(9):
                            q=await page.locator('#learn .v9-eq').inner_text();a,b=map(int,re.search(r'(\d+)\s*×\s*(\d+)',q).groups())
                            await page.locator('#learnAnswerV9').fill(str(a*b));await page.locator('#learn').get_by_role('button',name='答える',exact=True).click()
                            if i<8:await page.wait_for_function("document.getElementById('learnAnswerV9')?.value === ''")
                            else:await page.wait_for_selector('#learnTestAnswerV9')
                        for i in range(9):
                            q=await page.locator('#learn .v9-eq').inner_text();a,b=map(int,re.search(r'(\d+)\s*×\s*(\d+)',q).groups())
                            await page.locator('#learnTestAnswerV9').fill(str(a*b));await page.locator('#learn').get_by_role('button',name='答える',exact=True).click()
                            if i<8:await page.wait_for_function("document.getElementById('learnTestAnswerV9')?.value === ''")
                            else:await page.wait_for_function('S.learnHistory?.[2]?.passed === true')
                        raw=await page.evaluate("localStorage.getItem('kuku_preview_v5')")
                        fact=json.loads(raw)['f']['2x1'];self.assertEqual(fact['learnTestScore'],9);self.assertIn('learnedOn',fact);self.assertIs(fact['pendingLearn'],False)
                    elif variant=='balanced':
                        raw=await page.evaluate("() => {S.pet.xp=12;S.pet.care={study:4,play:4,food:4};S.pet.branch=null;branch();save();return localStorage.getItem('kuku_preview_v5')}")
                        self.assertEqual(json.loads(raw)['pet']['branch'],'balance')
                    elif variant in ['pending','invalid-score','invalid-date','invalid-pending']:
                        data=await page.evaluate('D()');fact=data['f']['2x1'];fact.update(learnTestScore=8,learnedOn='2026-10-31',pendingLearn=True)
                        if variant=='invalid-score':fact['learnTestScore']=10
                        if variant=='invalid-date':fact['learnedOn']='2026-99-99'
                        if variant=='invalid-pending':fact['pendingLearn']='false'
                        raw=json.dumps(data)
                    elif variant=='empty': raw=None
                    elif variant=='corrupt': raw='{oops'
                    else:
                        data=await page.evaluate('D()');data['auth_token']='synthetic-not-a-real-token';raw=json.dumps(data)
                    await page.evaluate("raw=>{if(raw===null)localStorage.removeItem('kuku_preview_v5');else localStorage.setItem('kuku_preview_v5',raw);localStorage.setItem('unrelated-auth-key','synthetic-do-not-export')}",raw)
                    await page.add_init_script("""(() => {window.storageReads=[];window.storageWrites=0;const get=Storage.prototype.getItem;Storage.prototype.getItem=function(k){storageReads.push(k);return get.call(this,k)};Storage.prototype.setItem=function(){storageWrites++;throw Error('No storage writes allowed on rescue page')};Storage.prototype.removeItem=function(){storageWrites++;throw Error('No storage removal allowed')};Storage.prototype.clear=function(){storageWrites++;throw Error('No storage clearing allowed')};})()""")
                    downloads=[];page.on('download',lambda item:downloads.append(item))
                    response=await page.goto(url+'/foremira-data-migration/kuku/',wait_until='networkidle');self.assertEqual(response.status,200)
                    self.assertEqual(await page.locator('#restore').count(),0)
                    self.assertEqual(await page.locator('#file').count(),0)
                    self.assertEqual(await page.locator('meta[name=robots]').get_attribute('content'),'noindex')
                    if variant in ['current','legacy','learned','balanced','pending']:
                        async with page.expect_download() as event:await page.locator('#export').click()
                        file=temp/(variant+'.json');await (await event.value).save_as(str(file));packet=json.loads(file.read_text())
                        self.assertEqual(packet['key'],KEY);self.assertEqual(packet['app'],'kuku-sodate');self.assertEqual(packet['version'],1);self.assertEqual(packet['data'],json.loads(raw))
                        self.assertNotIn('unrelated-auth-key',file.read_text());self.assertNotIn('synthetic-do-not-export',file.read_text())
                    else:
                        await page.locator('#export').click();self.assertTrue(await page.locator('#message').inner_text());self.assertEqual(downloads,[])
                    self.assertEqual(await page.evaluate('storageWrites'),0)
                    self.assertEqual(await page.evaluate("localStorage.getItem('kuku_preview_v5')"),raw)
                    self.assertEqual(set(await page.evaluate('storageReads')),{KEY})
                    self.assertFalse(outbound);self.assertFalse(errors)
                    await context.close()
            finally: await browser.close()
if __name__=='__main__': unittest.main()
