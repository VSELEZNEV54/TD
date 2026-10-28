# -*- coding: utf-8 -*-
"""Три состояния онлайн-урока для общего ролика возможностей."""
from blocks import ic


def render(stage, step):
    """Предметный UI, заголовок этапа и пояснение добавляет features.app."""
    stage = max(0, min(2, int(stage)))
    lesson_status = 'На связи' if stage == 0 else 'Идет урок'
    access = 'Доска у репетитора' if stage == 0 else 'Марине разрешено рисовать'
    material_status = 'К занятию' if stage == 0 else 'Открыто в уроке' if stage == 1 else 'Осталось в уроке'
    test_status = 'К занятию' if stage == 0 else 'Открыт во время урока' if stage == 1 else 'Готов к решению'
    saved = f'{ic("check", "ic ic--12")}Все записи сохранены' if stage == 2 else f'{ic("video", "ic ic--12")}Видео и доска рядом'
    answer = 'x₁ = 2, x₂ = 3' if stage else 'Найдем корни уравнения'
    return f'''<div class="fx-board-scene fx-board-stage-{stage}">
      <div class="fx-board-head"><b>Алгебра · Марина К.</b><span class="pill-now"><i></i>{lesson_status}</span></div>
      <div class="fx-board-layout">
        <div class="board fx-board-canvas">
          <div class="board__bar">
            <span class="fx-board-tools"><span class="fx-board-tool is-on">{ic('pen', 'ic ic--16')}</span><span class="fx-board-tool">{ic('eraser', 'ic ic--16')}</span><span class="fx-board-tool">{ic('type', 'ic ic--16')}</span><span class="fx-board-tool">{ic('shape', 'ic ic--16')}</span></span>
            <span class="board__sheet">Лист 1 / 2</span>
          </div>
          <div class="board__area fx-board-paper">
            <p class="fx-board-equation">x² − 5x + 6 = 0</p>
            <svg class="board__draw fx-board-drawing" viewBox="0 0 320 160" aria-hidden="true">
              <path class="board__axes" d="M16 132h288M92 10v142"/>
              <path class="board__curve" d="M36 22c16 92 40 112 70 112s52-26 66-112"/>
              <path class="board__line" d="M204 112h90"/>
              <circle class="fx-board-root" cx="96" cy="132" r="4"/><circle class="fx-board-root" cx="118" cy="132" r="4"/>
              <text class="fx-board-formula" x="204" y="72">D = 1</text>
              <text class="fx-board-result" x="204" y="102">2 и 3</text>
            </svg>
            <span class="board__cur fx-board-cursor"><i></i><b>Марина</b></span>
            <p class="fx-board-answer">{answer}</p>
          </div>
        </div>
        <div class="fx-board-cams">
          <div class="pd-cam"><span class="av av--lg av--me">АК</span><small>Анна · репетитор</small>{ic('mic', 'ic ic--12')}<span class="fx-board-camera">{ic('video', 'ic ic--12')}</span></div>
          <div class="pd-cam pd-cam--st"><span class="av av--lg">МК</span><small>Марина · ученица</small>{ic('mic', 'ic ic--12')}<span class="fx-board-camera">{ic('video', 'ic ic--12')}</span></div>
        </div>
      </div>
      <div class="fx-board-footer"><span class="chip chip--paid">{ic('pen', 'ic ic--12')}{access}</span><span class="fx-board-saved">{saved}</span></div>
      <div class="fx-board-resources">
        <div class="fx-board-resource">{ic('doc')}<span><b>Условия задач</b><small>{material_status}</small></span></div>
        <div class="fx-board-resource">{ic('task')}<span><b>Тест по теме</b><small>{test_status}</small></span>{ic('check', 'ic ic--12')}</div>
      </div>
    </div>'''
