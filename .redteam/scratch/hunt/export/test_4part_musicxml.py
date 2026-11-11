import sys
sys.path.insert(0, r"D:\aitraining")

from backend.importers import parse_musicxml_content

def test_four_part_musicxml():
    # 4-part MusicXML (one part per voice, standard format from MuseScore/Sibelius for choir)
    xml_4part = """<?xml version="1.0" encoding="UTF-8"?>
    <score-partwise version="3.1">
      <part-list>
        <score-part id="P1"><part-name>Soprano</part-name></score-part>
        <score-part id="P2"><part-name>Alto</part-name></score-part>
        <score-part id="P3"><part-name>Tenor</part-name></score-part>
        <score-part id="P4"><part-name>Bass</part-name></score-part>
      </part-list>
      <part id="P1">
        <measure number="1">
          <note><pitch><step>C</step><octave>5</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
        </measure>
      </part>
      <part id="P2">
        <measure number="1">
          <note><pitch><step>G</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
        </measure>
      </part>
      <part id="P3">
        <measure number="1">
          <note><pitch><step>E</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
        </measure>
      </part>
      <part id="P4">
        <measure number="1">
          <note><pitch><step>C</step><octave>3</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
        </measure>
      </part>
    </score-partwise>"""
    
    res = parse_musicxml_content(xml_4part)
    print("4-part MusicXML import result:")
    print("  soprano_melody count:", len(res["soprano_melody"]))
    print("  satb_voicings count:", len(res["satb_voicings"]))

if __name__ == "__main__":
    test_four_part_musicxml()
