/* Local-only, allowlisted learning-data transfer. No analytics or network requests. */
'use strict';
(() => {
 const KEY='kuku_preview_v5', MAX=1024*1024;
 const object=x=>x!==null && typeof x==='object' && !Array.isArray(x);
 const fail=()=>{throw new Error('対応していない、または壊れた学習データです。元の記録は変更していません。');};
 function fields(x,allowed){if(!object(x)||Object.keys(x).some(k=>!allowed.includes(k)))fail();}
 function number(x){if(typeof x!=='number'||!Number.isFinite(x)||x<0||x>1e15)fail();}
 function text(x){if(x!==null&&(typeof x!=='string'||x.length>1000))fail();}
 function validate(s){
  fields(s,['f','coins','streak','last','reward','settings','pet','dailyTask','economyVersion','lastTaskClear','taskStreak','learnHistory']);
  if(!object(s.f)||Object.keys(s.f).length!==81)fail();
  for(let a=1;a<=9;a++)for(let b=1;b<=9;b++){
   const f=s.f[`${a}x${b}`]; fields(f,['a','b','l','d','at','ok','w','ms','ca','cok','cms']);
   if(f.a!==a||f.b!==b||!Number.isInteger(f.l)||f.l < -1||f.l>20)fail();
   for(const k of ['d','at','ok','w','ms'])number(f[k]);
   for(const k of ['ca','cok','cms'])if(k in f)number(f[k]);
  }
  for(const k of ['coins','streak'])number(s[k]);
  for(const k of ['taskStreak','economyVersion'])if(k in s)number(s[k]);
  for(const k of ['last','reward','lastTaskClear'])if(k in s)text(s[k]);
  fields(s.settings,['challengeMin','species','dailyGoal','showReadings']);
  if(![1,3,5].includes(s.settings.challengeMin)||!['human','dino','animal'].includes(s.settings.species))fail();
  if('dailyGoal'in s.settings)number(s.settings.dailyGoal);
  if('showReadings'in s.settings&&typeof s.settings.showReadings!=='boolean')fail();
  fields(s.pet,['xp','branch','care','inv','log']); number(s.pet.xp);
  if(![null,'study','play','food'].includes(s.pet.branch))fail();
  fields(s.pet.care,['study','play','food']);for(const k of ['study','play','food'])number(s.pet.care[k]);
  fields(s.pet.inv,['food','toy','book','gem']);for(const k of ['food','toy','book','gem'])number(s.pet.inv[k]);
  if(!Array.isArray(s.pet.log)||s.pet.log.length>5000)fail();s.pet.log.forEach(text);
  if(s.dailyTask){fields(s.dailyTask,['date','correct','attempts','wrong','cleared']);text(s.dailyTask.date);for(const k of ['correct','attempts','wrong'])number(s.dailyTask[k]);if('cleared'in s.dailyTask&&typeof s.dailyTask.cleared!=='boolean')fail();}
  if(s.learnHistory){if(!object(s.learnHistory))fail();for(const [k,v]of Object.entries(s.learnHistory)){if(!/^[1-9]$/.test(k))fail();fields(v,['date','score','passed']);text(v.date);number(v.score);if(v.score>9||typeof v.passed!=='boolean')fail();}}
  return s;
 }
 function pack(raw){return {app:'kuku-sodate',version:1,key:KEY,createdAt:new Date().toISOString(),data:validate(JSON.parse(raw))};}
 function download(raw){const url=URL.createObjectURL(new Blob([JSON.stringify(pack(raw),null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='kuku-backup-'+Date.now()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 const $=id=>document.getElementById(id), message=s=>{$('message').textContent=s;};
 let pending=null,existing=null,backedUp=false;
 $('export').onclick=()=>{try{const raw=localStorage.getItem(KEY);if(raw===null)throw Error('このブラウザには九九の記録がありません。旧サイトで使ったブラウザ・通常/ホーム追加の起動方法を確認してください。');download(raw);backedUp=true;message('保存操作を開始しました。ファイルが保存できたことを確認してください。');}catch(e){message(e.message);}};
 if(document.body.dataset.exportOnly==='true')return;
 $('file').onchange=async e=>{pending=null;$('restore').disabled=true;try{
  const file=e.target.files[0];if(!file)return;if(file.size>MAX)fail();const packet=JSON.parse(await file.text());fields(packet,['app','version','key','createdAt','data']);
  if(packet.app!=='kuku-sodate'||packet.version!==1||packet.key!==KEY)fail();text(packet.createdAt);pending=validate(packet.data);
  existing=localStorage.getItem(KEY);backedUp=false;$('ack').checked=false;
  message(`読み込み確認：学習済み ${Object.values(pending.f).filter(f=>f.l>=0).length}問、${pending.coins}ポイント、育成 ${pending.pet.xp} XP。${existing===null?'このブラウザには既存記録がありません。':'既存記録があります。先に「記録を保存」で退避してください。'}`);$('restore').disabled=false;
 }catch(e){pending=null;message(e.message);}};
 $('restore').onclick=()=>{try{
  if(!pending)fail();if(!$('ack').checked)throw Error('内容と退避ファイルを確認してチェックしてください。');
  if(localStorage.getItem(KEY)!==existing)throw Error('別の画面で記録が変わりました。ファイルを選び直してください。');
  if(existing!==null&&!backedUp)throw Error('先に既存の記録をファイルへ保存してください。');
  if(!confirm('このブラウザの九九の記録を、確認したファイルの内容に置き換えますか？'))return;
  localStorage.setItem(KEY,JSON.stringify(validate(pending)));pending=null;$('restore').disabled=true;
  message('復元しました。他の九九画面を閉じてから、アプリを開き直してください。旧サイトとの自動同期はありません。');
 }catch(e){message(e.name==='QuotaExceededError'?'保存容量が不足しています。既存の記録は変更していません。':e.message);}};
})();
