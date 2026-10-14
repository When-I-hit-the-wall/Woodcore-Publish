"""FireTab's frame -- its own or a position plan's it follows --, its source shown in the form and the form's fields, and its tools -- a mixin of methods moved verbatim out of calc/tools/fire_tab.py (issue #30). FireTab names it among its bases.
"""

import json
from pathlib import Path
import project  # where the project this tab works on is (calc/project.py)
import theme  # the colours this tab states itself (theme.py)
import drawing_tab  # what every tab of plans drawn on imported documents shares (v0.115)
from drawing_tab import DrawingTab, number_text, plain_label
from domains import fire
from domains import plan as model
from fire_tab_build import DEFAULT_DOOR_CLASS, DEFAULT_DOOR_KIND, DEFAULT_SURFACE_KIND, DEFAULT_WALL_CLASS, HINTS, NAMES, TOOLS, FireTabBuildMixin  # split out of this module (issue #30): every name it had is still importable from it


PANE_TOOLS = ("crop", "calibrate")


OWN_FRAME_TOOLS = ("calibrate",)


# The units a frame's sheet is counted in, by its background's format: the position plan's own (plan_tab.UNITS).
UNITS = {"pdf": "pt", "png": "px", "jpg": "px", "svg": "", None: "pt"}


class FireTabFormMixin:
    """Methods of fire_tab.FireTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def own_frame(self):
        """Whether the plan carries a frame of its own, rather than following a position plan's."""
        return fire.follows(self.source) is None

    def frame(self):
        """What the plan is drawn over now: its own frame fields, or the position plan's it follows with its own crop over them (fire.frame_of)."""
        return fire.frame_of(self.source, self.plan_frames)[0]

    def followed_frame(self, source=None):
        """What the canvas is handed: the frame of the position plan `source` (the plan open) follows, as that plan states it -- an empty sheet for one that is gone --, or None for a plan with a frame of its own, which the canvas draws over the source itself. The plan's own crop is not in it: the canvas lays it over at every call (FireCanvas.frame_source), so a crop drawn, taken back or undone shows without the frame being handed over again."""
        source = self.source if source is None else source
        if fire.follows(source) is None:
            return None
        bare = {key: value for key, value in source.items() if key != "crop"}
        return fire.frame_of(bare, self.plan_frames)[0]

    def unit(self):
        background = self.frame().get("background")
        if not background:
            return UNITS[None]
        if Path(background["file"]).suffix.lower() in model.CAD_SUFFIXES:
            return ""  # a drawing's layout: hundredths of a millimetre of its page (calc/domains/cad.py)
        return UNITS.get(model.background_format(background["file"]), "")

    def refresh_frame(self, reload):
        """The canvas is shown the frame as it now is -- its background loaded again where that changed -- and what is drawn over it."""
        self.canvas.frame = self.followed_frame()
        if reload:
            self.canvas.load_background()
        self.canvas.invalidate()

    def frame_signature(self):
        frame = self.frame()
        return (json.dumps(frame.get("background"), sort_keys=True), json.dumps(frame.get("sheet"), sort_keys=True), fire.follows(self.source))

    def refresh_follow_items(self):
        """The combo of what the plan can follow: its own frame, then one entry per position plan -- `<id> — <name>` where it has one."""
        loading, self.loading = self.loading, True
        try:
            self.follow_combo.clear()
            self.follow_combo.addItem(self.t("fp_own_frame"), "")
            for pid, frame in self.plan_frames.items():
                name = frame.get("name") or frame.get("label") or ""
                self.follow_combo.addItem(f"{pid} — {name}" if name else pid, pid)
        finally:
            self.loading = loading

    def fill_follow(self):
        """The combo shows what the plan follows; a position plan that is gone is kept in it, marked, rather than silently replaced by whichever entry is first."""
        if self.follow_combo.count() != len(self.plan_frames) + 1:
            self.refresh_follow_items()
        pid = fire.follows(self.source) or ""
        for index in reversed(range(self.follow_combo.count())):
            if self.follow_combo.itemData(index) not in ([""] + list(self.plan_frames)):
                self.follow_combo.removeItem(index)
        index = self.follow_combo.findData(pid)
        if index < 0:
            self.follow_combo.addItem(self.t("fp_follow_item_gone", plan=pid), pid)
            index = self.follow_combo.count() - 1
        self.follow_combo.setCurrentIndex(index)

    def on_follow(self, _index):
        """Another frame: a position plan's, or its own. Following one removes the four frame fields; taking its own starts from the frame it followed, copied in (fire.detach), so that nothing jumps. Either is one step of «Annuler»."""
        if self.loading:
            return
        pid = self.follow_combo.currentData() or ""
        if pid == (fire.follows(self.source) or ""):
            return

        def apply():
            if pid:
                for key in fire.FRAME_KEYS:
                    self.source.pop(key, None)
                self.source["plan"] = pid
            else:
                detached = fire.detach(self.source, self.frame())
                detached["schema_version"] = fire.version_of(detached)
                self.source.clear()
                self.source.update(detached)
        self.edit(apply)
        self.refresh_frame(reload=True)
        self.canvas.fit()
        self.fill()
        if not self.own_frame() and self.canvas.tool in OWN_FRAME_TOOLS:
            self.choose_tool("select")

    def open_source(self, source, current_id, dirty):
        """Shows `source` over the frame it is drawn on -- the position plans read again, so a plan that follows one shows it as it now is."""
        self.plan_frames = fire.plan_frames(project.current().plans_dir)
        self.export_notes = []
        self.canvas.frame = self.followed_frame(source)
        super().open_source(source, current_id, dirty)

    def replace_source(self, state):
        """A step of «Annuler» or «Rétablir» put back: the source replaced by `state`, the frame handed to the canvas again and the background loaded again where it is another. An undo helper and never a writer (woodcore_gui.WRITERS)."""
        before = self.frame_signature()
        self.source.clear()
        self.source.update(state)
        self.refresh_frame(reload=self.frame_signature() != before)
        self.fill()
        self.on_changed()
        self.on_selection()

    def fill(self):
        """The form from the source -- a plan loaded, restored or undone."""
        self.loading = True
        try:
            self.identity.fill(self.source.get("name", ""), self.source.get("label", ""), self.source.get("id", ""), saved=self.current_id is not None)
            self.fill_follow()
            frame = self.frame()
            background = frame.get("background")
            doc = self.document(background.get("document")) if background and background.get("document") else None
            if background:
                page = int(background.get("page", 1))
                if doc is not None:
                    self.background_text.setText(self.t("plan_background_document", doc=drawing_tab.document_text(doc), page=page))
                else:
                    path = model.background_path(project.current().root, background["file"])
                    exists = path is not None and path.is_file()
                    self.background_text.setText(self.t("plan_background_file", file=background["file"], page=page) if exists
                                                 else self.t("plan_background_missing", file=background["file"]))
                self.opacity.slider.setValue(round(100 * float(background.get("opacity", model.DEFAULT_OPACITY))))
            else:
                self.background_text.setText(self.t("plan_no_background"))
                self.opacity.slider.setValue(round(100 * model.DEFAULT_OPACITY))
            for button in (self.rotate_left_button, self.rotate_right_button):
                button.setEnabled(doc is not None)
            self.background_import_button.setVisible(doc is None)
            scale = frame.get("scale")
            self.scale_mode.setCurrentIndex(0 if not scale else (1 if scale.get("mode") == "ratio" else 2))
            if scale and scale.get("mode") == "ratio":
                self.ratio_spin.setValue(int(scale.get("ratio", 100)))
            self.legend_check.setChecked("legend" in self.source)
            for key, slider in self.style_sliders.items():
                slider.setValue(int(round(100 * fire.drawing_factors(self.source)[key])))
        finally:
            self.loading = False
        self.update_legend_size()
        self.update_widgets()
        self.update_crop_text()

    def scale_text_of(self, frame):
        scale = frame.get("scale")
        per_m = fire.per_m(frame)
        if scale and scale.get("mode") == "ratio":
            return f"1:{scale.get('ratio')}"
        if scale and scale.get("mode") == "calibration" and per_m:
            return self.t("plan_calibration_text", k=number_text(per_m, 3), length=number_text(scale["length_m"], 3))
        return self.t("plan_scale_none")

    def update_widgets(self):
        """What is enabled, and what says why it is not: the controls of the plan's own frame while it follows a position plan's, the scale's own conditions otherwise."""
        own = self.own_frame()
        frame = self.frame()
        background = frame.get("background")
        is_pdf = bool(background) and model.background_format(background["file"]) == "pdf"
        mode = self.scale_mode.currentIndex()
        tip = self.t("fp_follow_tip")
        for widget, original in self.own_widgets:
            widget.setEnabled(own)
            widget.setToolTip(original if own else tip)
        self.opacity.setEnabled(own and bool(background))
        self.ratio_spin.setEnabled(own and mode == 1 and is_pdf)
        self.calibrate_button.setEnabled(own)
        self.calibrate_button.setToolTip(self.t("plan_calibrate_tip") if own else tip)
        scale = frame.get("scale") or {}
        if own and mode == 1 and not is_pdf:
            self.scale_text.setText(self.t("plan_ratio_pdf_only"))
        elif own and mode == 2 and scale.get("mode") == "calibration" and fire.per_m(frame):
            self.scale_text.setText(self.t("plan_calibration_text", k=number_text(fire.per_m(frame), 3), length=number_text(scale["length_m"], 3)))
        else:
            self.scale_text.setText("")
        self.follow_note.setVisible(not own)
        self.follow_info.setVisible(not own)
        self.background_text.setVisible(own)   # a plan that follows says its background in follow_info, with the scale
        if not own:
            shown = self.background_text.text() if background else self.t("plan_no_background")
            self.follow_info.setText(self.t("fp_follow_info", background=shown, scale=self.scale_text_of(frame)))

    def update_crop_text(self):
        """The crop card: the crop in force; and, for a plan that follows a position plan, whose it is -- the position plan's, until the plan states one of its own, which is then said in the orange of a value written over, with «Reprendre» to follow the position plan's again."""
        crop = model.crop_of(self.frame())
        self.crop_text.setText(self.t("plan_crop_text", w=number_text(crop["w"], 1), h=number_text(crop["h"], 1), unit=self.unit()))
        own = self.own_frame()
        stated = not own and "crop" in self.source
        self.reset_crop_button.setVisible(own)
        self.crop_state.setVisible(not own)
        self.crop_take_back_button.setVisible(stated)
        if own:
            return
        plan_id = fire.follows(self.source)
        self.crop_state.setText(self.t("fp_crop_own") if stated else self.t("fp_crop_followed", plan=plan_id))
        self.crop_state.setStyleSheet(f"color: {theme.colour('override')};" if stated else "")
        self.crop_take_back_button.setToolTip(self.t("fp_crop_take_back_tip", plan=plan_id))

    def on_meta(self, _text=None):
        if self.loading:
            return
        name, self.source["label"], self.source["id"] = self.identity.values()
        if name:
            self.source["name"] = name
        else:
            self.source.pop("name", None)
        self.on_changed()

    def on_opacity(self, value):
        if self.own_frame() and self.source.get("background"):
            self.edit(lambda: self.source["background"].__setitem__("opacity", round(value / 100, 2)))

    def update_legend_size(self):
        """The legend's size: its slider shows the factor the legend states, and is enabled only while there is a legend -- off, it says why."""
        on = "legend" in self.source
        tip = "" if on else self.t("fp_legend_size_tip")
        for widget in (self.legend_size, self.legend_slider):
            widget.setEnabled(on)
            widget.setToolTip(tip)
        loading, self.loading = self.loading, True
        try:
            self.legend_slider.setValue(int(round(100 * fire.legend_scale(self.source))))
        finally:
            self.loading = loading

    def on_legend_size(self, value):
        """The legend's own size (`legend.scale`): the plan's two factors leave it alone. One step of «Annuler» per drag."""
        if self.loading or "legend" not in self.source:
            return
        self.edit(lambda: self.source["legend"].__setitem__("scale", round(value / 100, 2)))

    def on_legend(self, checked):
        """The legend switched on -- where fire.legend_default puts it, a little in from the crop's corner -- or off. One step of «Annuler» either way."""
        if self.loading:
            return

        def apply():
            if checked:
                self.source["legend"] = fire.legend_default(self.frame())
            else:
                self.source.pop("legend", None)
        self.edit(apply)

    def on_scale_mode(self, index):
        if self.loading or not self.own_frame():
            return

        def apply():
            if index == 0:
                self.source.pop("scale", None)
            elif index == 1:
                self.source["scale"] = {"mode": "ratio", "ratio": self.ratio_spin.value()}
            else:
                scale = self.source.get("scale") or {}
                if scale.get("mode") != "calibration":
                    self.source.pop("scale", None)  # until the two points are clicked
        self.edit(apply)
        self.update_widgets()
        if index == 2 and not (self.source.get("scale") or {}).get("mode") == "calibration":
            self.choose_tool("calibrate")

    def on_ratio(self, value):
        if self.scale_mode.currentIndex() == 1 and self.own_frame():
            self.edit(lambda: self.source.__setitem__("scale", {"mode": "ratio", "ratio": value}))
            self.update_widgets()

    def on_calibrated(self, points):
        """A calibration drawn with the canvas's own tool -- on a plan with a frame of its own only: the tool is greyed while the plan follows a position plan."""
        if not self.own_frame():
            return
        length = self.ask_length()
        if length is None:
            return
        self.edit(lambda: self.source.__setitem__("scale", {"mode": "calibration", "points": [[round(x, 2), round(y, 2)] for x, y in points], "length_m": length}))
        self.loading = True
        self.scale_mode.setCurrentIndex(2)
        self.loading = False
        self.update_widgets()

    def reset_crop(self):
        self.edit(lambda: self.source.pop("crop", None))
        self.canvas.fit()

    def take_back_crop(self):
        """«Reprendre»: a plan that follows a position plan takes that plan's crop again -- in one step of «Annuler»."""
        if self.own_frame() or "crop" not in self.source:
            return
        self.edit(lambda: self.source.pop("crop", None))
        self.canvas.fit()

    def choose_tool(self, tool):
        if tool in OWN_FRAME_TOOLS and not self.own_frame():
            tool = "select"  # the scale is the position plan's: its button is greyed, a saved state may still ask
        if tool not in TOOLS + PANE_TOOLS:
            tool = "select"
        self.canvas.set_tool(tool)
        self.mark_tool(tool)
        self.hint.setText(self.t(HINTS[tool]))
        self.canvas.setFocus()

    def on_pointer(self, x, y, kind):
        frame = self.frame()
        text = self.t("plan_pointer", x=number_text(x, 1), y=number_text(y, 1), unit=self.unit())
        per_m = fire.per_m(frame)
        if per_m:
            crop = model.crop_of(frame)
            text += self.t("plan_pointer_m", x=number_text((x - crop["x"]) / per_m, 2), y=number_text((y - crop["y"]) / per_m, 2))
        self.pointer_line.setText(text)

    def on_surface_tool_kind(self, _index=None):
        """The kind of the next surface, chosen in the bar; the surfaces already drawn keep theirs (the selection's card changes them)."""
        kind = self.surface_combo.currentData()
        if kind is not None:
            self.canvas.zone_kind = kind

    def on_wall_tool_class(self, _index=None):
        """The fire resistance of the next wall, chosen in the bar; the walls already drawn keep theirs."""
        cls = self.wall_combo.currentData()
        if cls is not None:
            self.canvas.wall_class = cls
        self.canvas.update_helpers()   # the line being drawn is previewed in the colour of its resistance

    def on_door_tool_kind(self, _index=None):
        kind = self.door_kind_combo.currentData()
        if kind is not None:
            self.canvas.door_kind = kind
        self.canvas.update_helpers()

    def on_door_tool_class(self, _index=None):
        """The fire resistance of the next door -- none for «sans résistance», which the canvas keeps as None: such a door has no `class` at all."""
        self.canvas.door_class = self.door_class_combo.currentData() or None
        self.canvas.update_helpers()
