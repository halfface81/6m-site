// 首頁累積曲線:策略(實際線)與等權池,測試期虛線,0% 基準於正式起算日。
(function(){
  var D = window.__CUM;
  if(!D || !D.labels.length) return;
  var W=720,H=300,L=52,R=20,T=14,B=26,n=D.labels.length;
  var all=D.strat.concat(D.ew);
  var ymin=Math.min.apply(null,all)*0.98, ymax=Math.max.apply(null,all)*1.02;
  function X(i){return L+(W-L-R)*(n<2?0.5:i/(n-1));}
  function Y(v){return T+(H-T-B)*(1-(v-ymin)/(ymax-ymin));}
  function seg(a,from,to,dash){
    var s='';
    for(var i=from;i<=to;i++){s+=(i===from?'M':'L')+X(i).toFixed(1)+' '+Y(a[i]).toFixed(1)+' ';}
    return '<path d="'+s+'"'+(dash?' stroke-dasharray="4 4"':'')+'/>';
  }
  // y 刻度:挑 3~5 個整數百分比
  var ticks=[],lo=Math.ceil((ymin-1)*20)/20,hi=Math.floor((ymax-1)*20)/20;
  for(var v=lo;v<=hi+1e-9;v+=0.05){ticks.push(1+v);}
  if(ticks.length<2){ticks=[ymin,1,ymax];}
  var svg='<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="累積曲線：本策略與等權含息基準">';
  svg+='<g class="grid">';
  ticks.forEach(function(v){svg+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(v)+'" y2="'+Y(v)+'"/>';});
  svg+='</g><g class="axis">';
  ticks.forEach(function(v){
    var p=(v-1)*100, t=(p>0?'+':'')+p.toFixed(0)+'%';
    svg+='<text x="'+(L-6)+'" y="'+(Y(v)+3.5)+'" text-anchor="end">'+t+'</text>';});
  var step=Math.max(1,Math.floor(n/8));
  for(var i=0;i<n;i+=step){
    svg+='<text x="'+X(i)+'" y="'+(H-B+16)+'" text-anchor="middle" class="axis">'+D.labels[i]+'</text>';
  }
  svg+='</g>';
  // 測試期底色
  if(D.npre>0){
    svg+='<rect x="'+X(0)+'" y="'+T+'" width="'+(X(Math.max(D.npre-1,0))-X(0))+
      '" height="'+(H-T-B)+'" fill="var(--chip)" opacity=".5"/>';
  }
  svg+='<g class="series" style="stroke:var(--s-ew)">';
  if(D.npre>1) svg+=seg(D.ew,0,D.npre-1,true);
  if(n-D.npre>0) svg+=seg(D.ew,Math.max(D.npre-1,0),n-1,false);
  svg+='</g><g class="series" style="stroke:var(--s-strat)">';
  if(D.npre>1) svg+=seg(D.strat,0,D.npre-1,true);
  if(n-D.npre>0) svg+=seg(D.strat,Math.max(D.npre-1,0),n-1,false);
  svg+='</g></svg>';
  document.getElementById('cumWrap').innerHTML=svg;
})();
