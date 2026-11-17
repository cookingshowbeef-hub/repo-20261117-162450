"""Rebuild script_template.md with one V.O. block per voice line (short lines joined), pictures chosen for that line,
and keep the old pacing: old block ends get hold_after += (gap_block - gap_line); act_card shrinks by the same amount."""
import json, math, os, re, sys

PR = sys.argv[1]
C = os.path.join(PR, "04_Scripts_Code")
V = {
 "c0_01": 'px:854225 pb:20763', "c0_02": 'photo:korea_night#2 photo:korea_night#3@"to the west"', "c0_03": 'photo:korea_night#7 photo:korea_night#6@"a single small" photo:pyongyang#19@"the capital"',
 "c0_04": "px:8978968 photo:pyongyang#18", "c0_05": "photo:portraits#11 photo:pyongyang#22 px:29853743", "c0_06": "px:4045055 px:5818973",
 "c0_08": "px:5555355 pb:66601 px:6848983 px:4106152",
 "a1_01": "px:11053853 pb:175213 px:6130032 px:14898347", "a1_02": "px:11194735", "a1_03": "pb:66598 px:8677058",
 "a1_04": "px:6212891 px:8869921 px:6549528", "a1_05": "pb:349087 px:6549976", "a1_06": "px:5674557 px:7545824",
 "a1_07": "photo:kim_il_sung#4 photo:kim_il_sung#2 photo:pyongyang#20",
 "a1_08": "px:31959277 px:11272050 px:14306928 photo:kim_il_sung#5 px:4230107", "a1_09": "px:4045055 pb:111281",
 "a1_10": 'photo:pyongyang#12 photo:kim_il_sung#1@"study at" photo:pyongyang#2@"join the party" px:36024529@"food rations"',
 "a1_11": 'px:27956613 px:39898853@"you might" px:31752064@"made to" px:39894176@"with almost"', "a1_12": "px:7830309 px:9029219 px:8869921",
 "a1_13": "px:26241968 px:39346859", "a1_14": "px:13020380 pb:243239",
 "a2_01": "photo:portraits#6 px:7317422 px:10646296", "a2_02": "photo:portraits#5 photo:portraits#9", "a2_03": "photo:portraits#0 photo:portraits#2",
 "a2_04": 'px:4440684 photo:portraits#13@"local officials" pb:20459@"a speck"', "a2_05": 'photo:portraits#9 px:6937884@"when their" photo:portraits#6@"rushed in"', "a2_06": 'photo:mass_games#11 px:8363868@"at nursery" pb:267@"may be taught"',
 "a2_07": 'photo:portraits#7 px:29130948@"was born" pb:35304@"a new star" photo:paektu#0@+11.5', "a2_08": "pb:132370 px:39442147", "a2_09": "photo:pyongyang#26 px:11124661",
 "a2_11": "px:2108274 px:39758763", "a2_12": "pb:44648 px:4106152",
 "a3_01": "photo:nk_school#14 photo:nk_school#11 px:36205613", "a3_02": "photo:nk_school#2 photo:nk_school#6",
 "a3_03": 'photo:mass_games#1 photo:portraits#10@"recite an oath" photo:nk_school#11@"your mother"', "a3_04": "photo:nk_school#7 photo:mass_games#2",
 "a3_05": "photo:nk_school#9 px:8363868 photo:mass_games#10", "a3_06": "photo:pyongyang#3 photo:pyongyang#4",
 "a3_07": "photo:mass_games#5 photo:mass_games#0 photo:mass_games#4", "a3_08": "photo:pyongyang#25 px:6061760",
 "a3_09": 'px:39878858 px:32312326@"in spring" px:34842120@"in autumn"', "a3_10": 'pb:223170 px:31025293@"scrap paper" px:31025289@"if it falls"',
 "a3_11": "photo:mass_games#3 photo:mass_games#7 photo:mass_games#8 photo:mass_games#13", "a3_13": "photo:mass_games#6 photo:mass_games#9",
 "a4_01": "px:9431644 photo:pyongyang#28 px:33857212", "a4_02": "photo:pyongyang#29 px:7292659", "a4_03": "px:7292647 px:6016323",
 "a4_04": 'px:6657871 pb:20837@"sometimes there are" px:28556160@"middle of"', "a4_05": "photo:portraits#10", "a4_06": "photo:portraits#14 photo:nk_school#7 px:7706071",
 "a4_07": "photo:portraits#11 photo:portraits#1", "a4_08": "px:35876587 photo:portraits#3", "a4_09": "px:8319633 px:10295574 pb:45249",
 "a4_10": "px:4523130 px:7055028", "a4_12": 'px:15069621 pb:88738@"a law passed" px:15069622@"especially"', "a4_13": "px:32067544 px:2845957",
 "a4_14": "pb:39292 px:9807458", "a4_16": 'px:7457401 px:40806778@"streets flooded" pb:21116@"however they"', "a4_17": "px:3290546 px:4106152",
 "a5_01": "px:34393391 px:11272050", "a5_02": "photo:kim_il_sung#0 photo:kim_il_sung#3 px:32934424", "a5_03": "px:18153515",
 "a5_04": 'photo:nk_country#25 px:4667199@"stopped working" pb:31470@"people ate" px:20521976@"anything that"', "a5_05": "photo:nk_country#21 px:4100312", "a5_06": "px:5674557 photo:nk_country#9 px:7234789",
 "a5_07": "photo:nk_country#26", "a5_08": 'px:10483340 px:36066725@"brought goods" px:35878664@"laid out" px:20450812@"on the pavement"', "a5_09": "photo:markets#5",
 "a5_10": "px:8785817 px:40902578 px:34391808", "a5_11": "px:5562568", "a5_12": 'px:14047047 px:36068162@"which may" px:35923575@"his wage"',
 "a5_13": 'px:40961892 px:4518676@"chinese noodles" px:6266924@"slip money"', "a5_14": "px:35000996", "a5_15": "px:40961882",
 "a5_16": 'photo:pyongyang#26 photo:portraits#4@"world of slogans" px:34579094@"world of money"', "a5_17": "px:6326929",
 "a6_01": "pb:43185 px:13625837 px:35332817", "a6_02": "photo:nk_military#12 px:34580598", "a6_03": "photo:nk_military#3 px:38313921",
 "a6_04": "photo:nk_military#18 photo:mass_games#10", "a6_05": "px:12160811", "a6_06": "pb:3577 pb:223459 px:4012942",
 "a6_07": 'photo:mass_games#10 px:27104380@"sent to build" px:30062105@"dig canals"', "a6_08": "px:20498440 px:3958688", "a6_09": "px:24812142",
 "a6_10": "px:26604369 photo:portraits#10 photo:pyongyang#20 px:35650213", "a6_11": "px:24800203",
 "a7_01": "photo:pyongyang#18 px:35186909 photo:pyongyang#10", "a7_03": "photo:pyongyang#15 px:37932726",
 "a7_04": "pb:421 photo:pyongyang#16 px:34393391", "a7_05": "px:7981526 px:7981534", "a7_06": "px:6581406 pb:60266",
 "a7_07": "photo:un_coi#0 px:5988814 pb:60265 px:32067544", "a7_08": "px:30308829 px:2845945 px:10475103 px:10577855",
 "a7_09": "px:10577776 px:29834229", "a7_10": "px:7924460", "a7_11": "pb:46308", "a7_12": "px:5490544 px:4122173",
 "a8_01": "px:35629930 pb:90453", "a8_02": "px:3427514", "a8_03": "photo:yalu#11 photo:tumen#0", "a8_04": "photo:tumen#7 photo:tumen#4",
 "a8_05": "photo:korea_night#2 photo:korea_night#5", "a8_06": "px:10466832", "a8_07": 'px:40463696 px:5944981@"to wade" photo:tumen#5@"and once"',
 "a8_08": "px:35839120", "a8_09": "px:28812638 px:28812647", "a8_10": "photo:defectors#0 px:37932726", "a8_11": "px:7981534 px:6016323",
 "a8_12": 'photo:tumen#9 pb:329674@"even more" px:5988811@"the number"', "a8_13": "px:9897055 photo:china_border_town#1 pb:26793", "a8_15": "photo:portraits#6 pb:20459",
 "c9_01": "pb:15026 px:40011477 px:11354012", "c9_02": "photo:nk_school#14 px:34391808 px:5562568", "c9_03": "photo:portraits#11 px:38136563",
 "c9_04": "px:8862328 photo:mass_games#9", "c9_05": "photo:korea_night#3", "c9_06": "px:4156415 photo:korea_night#0", "c9_07": "pb:3577",
 "c9_08": "px:5921369", "c9_09": "px:35889601 photo:korea_night#6",
}
JOIN = {"c0_06": "c0_07", "a2_09": "a2_10", "a3_11": "a3_12", "a4_10": "a4_11", "a4_14": "a4_15", "a4_17": "a4_18", "a7_01": "a7_02", "a8_13": "a8_14"}
ACTS = {"c0": 'COLD OPEN — "The Last Light"', "a1": 'ACT ONE — "A Fate Already Written"', "a2": 'ACT TWO — "Two Portraits on the Wall"',
        "a3": 'ACT THREE — "The Red Scarf"', "a4": 'ACT FOUR — "Under the Eyes of the Collective"', "a5": 'ACT FIVE — "The Hungry Years"',
        "a6": 'ACT SIX — "Ten Years in Uniform"', "a7": 'ACT SEVEN — "The Invisible Line"', "a8": 'ACT EIGHT — "The River"', "c9": "CLOSING"}

TL = json.load(open(os.path.join(PR, "05_Renders", "timeline.json"), encoding="utf-8"))
NARR = {p["id"]: p for p in json.load(open(os.path.join(PR, "01_Voice", "narration.json"), encoding="utf-8"))}
old_ends = [b["lines"][-1] for b in TL["blocks"]]
ids = [l["id"] for l in TL["lines"]]
act_last = {}
for i in ids:
    act_last[i[:2]] = i

cfg_p = os.path.join(C, "film.json")
cfg = json.load(open(cfg_p, encoding="utf-8"))
T = cfg["timing"]
gl, gb = T["gap_line"], T.get("gap_block", 1.8)
extra = round(gb - gl, 3)
if extra > 0:
    hold = dict(T.get("hold_after", {}))
    for e in old_ends:
        if e != act_last[e[:2]]:
            hold[e] = round(hold.get(e, 0) + extra, 3)
    T["hold_after"], T["gap_block"], T["act_card"] = hold, gl, round(T.get("act_card", 5.5) - extra, 3)
    json.dump(cfg, open(cfg_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

head = open(os.path.join(C, "script_template.md"), encoding="utf-8").read()
head = head[:head.index("## COLD OPEN")]
out, act, skip = [head], None, set(JOIN.values())
for i in ids:
    if i in skip:
        continue
    if i[:2] != act:
        act = i[:2]
        out.append(f"---\n\n## {ACTS[act]} ({{{{T:{act}}}}})\n")
    grp = [i] + ([JOIN[i]] if i in JOIN else [])
    codes = re.findall(r'\S+@"[^"]*"|\S+', V[i])
    words = " / ".join(NARR[g]["text"][:60] for g in grp)
    out.append(f"**VISUAL:** {', '.join(codes)}  — for: {words}\n\n{{{{{' '.join(grp)}}}}}\n")
out.append("## PRODUCTION NOTES\n\nAnything below this heading is ignored by the pipeline.\n"
           "- One block per voice line (very short lines joined), so each picture sits under the sentence it illustrates.\n")
open(os.path.join(C, "script_template.md"), "w", encoding="utf-8").write("\n".join(out))
print("blocks:", sum(1 for i in ids if i not in skip), "| act_card", T["act_card"], "| gap_block", T["gap_block"])
