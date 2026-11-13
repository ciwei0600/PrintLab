export default function AppearanceWorkflow({workflow:w}) {
  if (!w || w.phase==='not_configured') return null;
  const titles={internal_revision:'内部对照与调整',awaiting_user_review:'已达提交门槛 · 待你审稿',appearance_confirmed:'外观已由你确认'};
  const score=Number.isFinite(w.score)?`${Math.floor(w.score*100)/100} / 100`:'未评分';
  return <section className="appearance-workflow" aria-label="外观审稿流程">
    <div className="section-heading"><div><span className="section-eyebrow">当前版本 {w.revision||'待建立'}</span><h2>{titles[w.phase]||'内部对照与调整'}</h2></div><strong className="appearance-score">相似度内审：{score}</strong></div>
    <p className="appearance-steps">选定设计稿 → 外观建模 → 对照评分 ↔ 调整 → 你审稿确认 → 结构设计</p>
    <p>轮廓 30% · 比例 20% · 曲面 20% · 特征位置 20% · 细节 10%。这是附对照证据的视觉评分。</p>
    <p>{w.phase==='internal_revision'?'证据完整、关键特征通过且总分达到 90 / 100 后，才提交你审稿。未达标继续内部调整。':w.phase==='awaiting_user_review'?'内审已达到 90 / 100 提交门槛。请在对话里确认外观或提出修改；确认前不进入正式结构与制作。':'后续改动若影响外形，需要重新对照评分并由你确认。'}</p>
    <small>外观确认与打印授权分别记录；评分和外观确认均不会启动打印。</small>
  </section>;
}
