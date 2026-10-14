async function request(path, options = {}) {
  const response = await fetch(path, {cache:'no-store', ...options});
  if (!response.ok) throw new Error('요청 실패 (' + response.status + ')');
  return response.json();
}
Promise.all([request('/health'), request('/api/info')]).then(([health, info]) => {
  if (health.status !== 'ok') throw new Error('헬스체크 실패');
  document.getElementById('status').textContent = '서버 응답 정상';
  document.getElementById('version').textContent = info.version;
  document.getElementById('region').textContent = info.region;
}).catch(() => {document.getElementById('status').textContent = '연결 실패 · 새로고침해 주세요';});
function bind(formId, resultId, action) {
  document.getElementById(formId).addEventListener('submit', async event => {
    event.preventDefault();const button=event.target.querySelector('button');button.disabled=true;
    try {document.getElementById(resultId).textContent = await action();}
    catch (error) {document.getElementById(resultId).textContent = error.message;}
    finally {button.disabled=false;}
  });
}
bind('greeting','response',async()=> (await request('/api/hello?name='+encodeURIComponent(document.getElementById('name').value))).message);
bind('echo','echo-response',async()=> {const result=await request('/api/echo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:document.getElementById('message').value})});return result.message+' ('+result.length+'자)';});
