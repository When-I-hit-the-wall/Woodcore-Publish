// The report's language, and every word the engine prints in it (docs/typst/language.md §4bis).
//
// One glossary, `calc/i18n/strings.json`, read here and by `calc/i18n/strings.py` -- so a word both
// sides say, such as the note under a connection's figure that Python sizes and Typst fills in, is
// written once. What is *not* in it is the engineer's own data: descriptions and text values,
// case names, positions, material names, the prose of Sections/*.typ. That is the whole rule
// `tl` applies -- a string is translated if the glossary carries it, and passes through if not.
//
// Two ways in, because Typst's state can only be read inside `context`:
//
//   `t-of(lang, key)` / `tl-of(lang, text)`   plain strings, for a caller that has already resolved
//                                             the language -- every show-* function, which is inside
//                                             a context block anyway, and every string written into
//                                             an SVG or into math source.
//   `t(key)` / `tl(text)`                     content, wrapped in `context`, for markup:
//                                             `#t("governing")`, `#tl(get(v, "label"))`.
//
// ⚠️ A section file calls neither (docs/typst/language.md §4bis, v0.54). Its headings, and the document's
// title, are the engineer's own words, written by hand in the language the report is written in, and
// nothing translates them -- which is why the glossary carries no `section.*` key any more.

// The glossary itself, the same file calc/i18n/strings.py reads. Relative to this file, like the
// data/ paths beside it, so it does not depend on where --root points.
#let glossary = json("../calc/i18n/strings.json")

// The languages a report can be written in. The first is the source language: the German the export
// itself carries, and the key of the glossary's `terms` block.
#let report-languages = ("de", "fr", "en")
#let source-language = report-languages.first()

#assert(
  glossary.languages == report-languages,
  message: "i18n: strings.json declares the languages " + repr(glossary.languages)
    + " -- lib/i18n.typ expects " + repr(report-languages),
)

/// The report's language, set once in `Statischer Rapport.typ` (docs/typst/language.md §4bis). Every word
/// the engine prints follows it; the engineer's own prose in Sections/ does not.
///
/// ```typ
/// #context report-language.get()
/// ```
///
/// ```typ
/// #set-report-language("fr")
/// #context [Die Engine schreibt in #report-language.get().]
/// ```
///
/// -> state
#let report-language = state("report-language", source-language)

/// Sets the language the engine prints in: "de", "fr" or "en" -- every word it composes itself, the labels,
/// captions, legends and footnotes. Typst's own words («Abbildung», the outline's title, the hyphenation) follow
/// `config.typ`'s `doc-lang`, a setting of its own. The one command the entry point adds, beside
/// `report-level.update` and `number-digits.update`. Put it before the first thing the engine prints: like
/// every state, it reaches only what follows it, and `config.typ` reads no state (docs/typst/language.md §4bis).
///
/// ```typ
/// #set-report-language("fr")
/// #var("s_k", domain: ("snow-load", "SL"), level: 2)
/// ```
///
/// ```typ
/// #set-report-language("en")
/// #include domain-file("live-load", "A1")
/// ```
///
/// - lang (str): "de", "fr" or "en".
/// -> content
#let set-report-language(lang) = {
  // panic inside an `if`: an assert builds its message before it tests, and `"…" + lang` failed on «cannot add string and integer» for a language given as a number (v0.86)
  if not (lang in report-languages) {
    panic("set-report-language: no language " + repr(lang) + " -- valid languages: " + report-languages.join(", "))
  }
  report-language.update(lang)
}

/// The language in force here. Reads the state, so it must be called inside `context` -- which every
/// show-* function already is, for the report level.
///
/// ```typ
/// #context report-lang()
/// ```
///
/// ```typ
/// #context if report-lang() == "de" [Deutsch] else [eine andere Sprache]
/// ```
///
/// -> str
#let report-lang() = report-language.get()

// --- The glossary -----------------------------------------------------------------
// A template's holes, `{sheet}`, `{area}`, are found and split on with one regex. The captures are
// keyed by the hole's *name*, never by its position, so a language that orders them differently from
// the German still comes out right.

#let hole-pattern = regex("\\{(\\w+)\\}")
#let template-segments(pattern) = pattern.split(hole-pattern)
#let template-holes(pattern) = pattern.matches(hole-pattern).map(m => m.captures.first())

#let fill-template(pattern, values) = {
  let out = pattern
  for (name, value) in values {
    out = out.replace("{" + name + "}", value)
  }
  assert(
    not out.contains(regex("\\{\\w+\\}")),
    message: "i18n: nothing given for a hole of \"" + pattern + "\"",
  )
  out
}

/// One of the engine's own words, as a string, in the language given.
///
/// ```typ
/// #t-of("fr", "governing")
/// ```
///
/// ```typ
/// #for l in ("de", "fr", "en") [ #l: #t-of(l, "governing") \ ]
/// ```
///
/// - lang (str): "de", "fr" or "en".
/// - key (str): a key of the glossary's `engine` or `templates` block.
/// - ..values (str): one named argument per hole of a template, e.g. `sheet: "SL"`.
/// -> str
#let t-of(lang, key, ..values) = {
  if not (lang in report-languages) {
    panic("t-of: no language " + repr(lang) + " -- valid languages: " + report-languages.join(", "))
  }
  let named = values.named()
  if key in glossary.engine {
    assert(named.len() == 0, message: "t-of: \"" + key + "\" takes no arguments")
    glossary.engine.at(key).at(lang)
  } else if key in glossary.templates {
    fill-template(glossary.templates.at(key).at(lang), named)
  } else {
    panic("t-of: no string \"" + key + "\" in the glossary -- see calc/i18n/strings.json")
  }
}

// The template `text` was composed from, as `(key, captures)`, or `none`. The German is what is
// matched -- the export carries no other language -- and matching is done on the literal segments
// around the holes, which needs no regular expression and cannot be confused by a sheet's name.
#let match-template(text) = {
  let found = none
  for (key, entry) in glossary.templates {
    if found != none { continue }
    let pattern = entry.at(source-language)
    let parts = template-segments(pattern)
    if parts.len() < 2 { continue }
    if not text.starts-with(parts.first()) or not text.ends-with(parts.last()) { continue }
    let rest = text.slice(parts.first().len())
    let captures = ()
    let ok = true
    for part in parts.slice(1, parts.len() - 1) {
      if not ok { continue }
      let cut = rest.position(part)
      if part == "" or cut == none {
        ok = false
      } else {
        captures.push(rest.slice(0, cut))
        rest = rest.slice(cut + part.len())
      }
    }
    let tail = parts.last()
    if ok and rest.len() >= tail.len() {
      captures.push(if tail == "" { rest } else { rest.slice(0, rest.len() - tail.len()) })
      let names = template-holes(pattern)
      if names.len() == captures.len() and captures.all(c => c != "") {
        let values = (:)
        for (i, name) in names.enumerate() { values.insert(name, captures.at(i)) }
        found = (key: key, values: values)
      }
    }
  }
  found
}

/// A string the data carries, in the language given: a term of the glossary, else the template it was
/// composed from, else itself. Unchanged is the safe and the usual answer -- a material's name, a
/// description, a case's name and a value the engineer typed are not the engine's words.
///
/// ```typ
/// #tl-of("fr", "Bezugshöhe")
/// ```
///
/// ```typ
/// #for l in ("de", "fr", "en") [ #l: #tl-of(l, "Schneelast") \ ]
/// ```
///
/// - lang (str): "de", "fr" or "en".
/// - text (str): the German the export carries.
/// -> str
#let tl-of(lang, text) = {
  // a language the glossary does not carry is refused whatever the text: it passed for a word nothing matched and crashed on one it knew, «dictionary does not contain key "it"» (v0.86)
  if not (lang in report-languages) {
    panic("tl-of: no language " + repr(lang) + " -- valid languages: " + report-languages.join(", "))
  }
  if lang == source-language or type(text) != str or text == "" {
    text
  } else if text in glossary.terms {
    glossary.terms.at(text).at(lang)
  } else {
    let found = match-template(text)
    if found == none {
      text
    } else {
      // a hole the template lists under `translate` carries a norm's word, and goes through the terms too
      let entry = glossary.templates.at(found.key)
      let values = found.values
      for name in entry.at("translate", default: ()) {
        let word = values.at(name)
        if word in glossary.terms { values.insert(name, glossary.terms.at(word).at(lang)) }
      }
      fill-template(entry.at(lang), values)
    }
  }
}

/// One of the engine's own words, as a string, in the report's language. What the engine itself calls
/// at every print site: it reads the state, so it needs an enclosing `context` -- and every show-*
/// function is one, which is why no helper of the engine had to grow a `lang` parameter.
///
/// ```typ
/// #context [#t-str("governing")]
/// ```
///
/// ```typ
/// #context [#upper(t-str("governing"))]
/// ```
///
/// - key (str): a key of the glossary's `engine` or `templates` block.
/// - ..values (str): one named argument per hole of a template.
/// -> str
#let t-str(key, ..values) = t-of(report-lang(), key, ..values)

/// A string the data carries, in the report's language. The engine's own call, like `t-str`: inside a
/// context, and a string rather than content, so it also serves math source and SVG text.
///
/// ```typ
/// #context [#tl-str("Schneelast")]
/// ```
///
/// ```typ
/// #set-report-language("fr")
/// #context [#tl-str("Bezugshöhe")]
/// ```
///
/// - text (str): the German the export carries.
/// -> str
#let tl-str(text) = tl-of(report-lang(), text)

/// One of the engine's words followed by its colon, set the way each language sets one: French keeps a
/// narrow no-break space before it, German and English do not. The same rule Woodcore's window applies
/// to its own field names. It reads the report's language, so it is called inside `context`.
///
/// ```typ
/// #context [#t-label("moisture_class") 1]
/// ```
///
/// ```typ
/// #set-report-language("fr")
/// #context [#t-label("moisture_class") 1]
/// ```
///
/// - key (str): a key of the glossary's `engine` or `templates` block.
/// - ..values (str): one named argument per hole of a template.
/// -> str
#let t-label(key, ..values) = {
  t-str(key, ..values) + (if report-lang() == "fr" { "\u{202f}:" } else { ":" })
}

/// A template with its holes left standing, in the report's language -- for a sentence whose hole is a
/// piece of *math* rather than a word (`I_p` in mm², `F_3`): split the pattern on the hole and set the
/// math between the halves, which a plain string could not carry. It reads the report's language, so it
/// is called inside `context`.
///
/// ```typ
/// #context [#t-pattern("connection.caption")]
/// ```
///
/// ```typ
/// #set-report-language("fr")
/// #context [#t-pattern("connection.caption")]
/// ```
///
/// - key (str): a key of the glossary's `templates` block.
/// -> str
#let t-pattern(key) = {
  assert(key in glossary.templates, message: "t-pattern: no template \"" + key + "\"")
  glossary.templates.at(key).at(report-lang())
}

/// One of the engine's own words, as content, in the report's language -- for a caller in markup
/// rather than inside a show-* function: `#t("governing")`, `#t("connection.caption", id: "VU-MP-1")`.
/// Not for a heading: those are the engineer's, and are written by hand (docs/typst/language.md §4bis).
///
/// ```typ
/// #t("governing")
/// ```
///
/// ```typ
/// #set-report-language("fr")
/// #t("governing") -- #t("with")
/// ```
///
/// - key (str): a key of the glossary's `engine` or `templates` block.
/// - ..values (str): one named argument per hole of a template.
/// -> content
#let t(key, ..values) = context t-of(report-lang(), key, ..values)

/// A string the data carries, as content, in the report's language. The counterpart of `t` for a
/// label read from `data/`, for a caller in markup rather than inside a show-* function.
///
/// ```typ
/// #tl("Bezugshöhe")
/// ```
///
/// ```typ
/// #set-report-language("fr")
/// #tl("Bezugshöhe") -- #tl("Schneelast")
/// ```
///
/// - text (str): the German the export carries.
/// -> content
#let tl(text) = context tl-of(report-lang(), text)
