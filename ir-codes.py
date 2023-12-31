"""
Yamaha YSP-4000 IR codes from https://forum.arduino.cc/t/yamaha-ysp-4000-ir-hex-codes-and-how-to-store-them-for-an-esp8266-12e/487761/3

There is also one interesting post about bruteforcing codes: https://nobbin.net/2012/12/08/converting-yamaha-nec-infrared-codes-to-lirc-format/
"""

ir_codes = {
    "PWR_TOGGLE": "0x1EE133CC",
    "MUTE_TOGGLE": "0x1EE139C6",
    "FM_XM": "0x1EE1D22D",
    "TV_STB": "0x1EE1FB04",
    "DVD": "0x1EE152AD",
    "AUX1": "0x1EE1926D",
    "AUX2": "0x1EE17B84",
    "AUX3": "0x1EE13DC2",
    "INPUT_MODE": "0x1EE1B14E",
    "VOL_UP": "0x1EE17887",
    "VOL_DOWN": "0x1EE1F807",
    "SLEEP_TIMER": "0x1EE1F20D",
    "TEN_KEY0": "0x1EE108F7",
    "TEN_KEY1": "0x1EE18877",
    "TEN_KEY2": "0x1EE148B7",
    "TEN_KEY3": "0x1EE1C837",
    "TEN_KEY4": "0x1EE128D7",
    "TEN_KEY5": "0x1EE1A857",
    "TEN_KEY6": "0x1EE16897",
    "TEN_KEY7": "0x1EE1E817",
    "TEN_KEY8": "0x1EE118E7",
    "TEN_KEY9": "0x1EE19867",
    "PRESET_PLUS": "0x1EE1D827",
    "PRESET_MINUS": "0x1EE138C7",
    "ABCDE_PLUS": "0x1EE1B847",
    "ABCDE_MINUS": "0x1EE1DD22",
    "TUNING_PLUS": "0x1EE155AA",
    "TUNING_MINUS": "0x1EE1956A",
    "PRESET_TUNE": "0x1EE115EA",
    "SEARCH_MODE": "0x1EE1ED12",
    "MEMORY": "0x1EE14DB2",
    "XM_ENTER": "0x1EE1BD42",
    "XM_DISPLAY": "0x1EE11DE2",
    "SURROUND": "0x1EE19966",
    "DSP_MOVIE": "0x1EE19B64",
    "DSP_MUSIC": "0x1EE15BA4",
    "DSP_SPORTS": "0x1EE1DB24",
    "DSP_OFF": "0x1EE1D926",
    "MUSIC_ENHANCER": "0x1EE1D32C",
    "VOLUME_MODE": "0x1EE151AE",
    "SRS_TRUBASS": "0x1EE1D12E",
    "SOUND_LEVEL": "0x1EE112ED",
    "DOLBY_TEST": "0x1EE1FA05",
    "BEAM_5": "0x1EE143BC",
    "BEAM_ST_3": "0x1EE1C33C",
    "BEAM_3": "0x1EE123DC",
    "BEAM_STEREO_5CH": "0x1EE10AF5",
    "BEAM_MY": "0x1EE1A35C",
    "BEAM_SURROUND": "0x1EE1639C",
    "SET_MENU": "0x1EE1B946",
    "INTELLIBEAM": "0x1EE1C53A",
    "UP": "0x1EE1718E",
    "DOWN": "0x1EE1F10E",
    "RIGHT": "0x1EE17986",
    "LEFT": "0x1EE1F906",
    "ENTER": "0x1EE1837C",
    "RETURN": "0x1EE103FC",
    "POWER_ON": "0x1EE17E81",
    "POWER_OFF": "0x1EE1FE01",
    "MUTE_ON": "0x7E8145BA",
    "MUTE_20DB": "0x7E81FB04",
    "MUTE_OFF": "0x7E81C53A",
    "INPUT_FM": "0x1EE16D92",
    "INPUT_XM": "0x1EE1BE41",
    "INPUT_AUTO": "0x7E81659A",
    "DTS": "0x7E8115EA",
    "ANALOG": "0x7E8155AA",
    "AAC": "0x7E81DC23",
    "SLEEP_OFF": "0x7E81CD32",
    "SLEEP_120": "0x7E812DD2",
    "SLEEP_90": "0x7E81AD52",
    "SLEEP_60": "0x7E816D92",
    "SLEEP_30": "0x7E81ED12",
    "PRESET_PAGE_A": "0x1EE1F50A",
    "PRESET_PAGE_B": "0x1EE1758A",
    "PRESET_PAGE_C": "0x1EE1B54A",
    "PRESET_PAGE_D": "0x1EE135CA",
    "PRESET_PAGE_E": "0x1EE1D52A",
    "AUTOSEARCH_PLUS": "0x1EE18D72",
    "AUTOSEARCH_MINUS": "0x1EE10DF2",
    "SEARCH_ALL": "0x1EE1E619",
    "SEARCH_PRESET": "0x1EE116E9",
    "NIGHT_CINEMA": "0x7E81D926",
    "NIGHT_MUSIC": "0x7E81F30C",
    "NIGHT_OFF": "0x7E8139C6",
    "TV_MODE_ON": "0x1EE13EC1",
    "TRUBASS_DEEP": "0x1EE17689",
    "TRUBASS_MID": "0x1EE1B649",
    "TRUBASS_OFF": "0x1EE1F609",
    "BEAM_5CH": "0x7E81FF00",
    "PRO_LOGIC": "0x7E81BF40",
    "PROLOGIC_MOVIE": "0x7E81E619",
    "PROLOGIC_MUSIC": "0x7E8116E9",
    "PROLOGIC_GAME": "0x7E81E31C",
    "NEO6_MOVIE": "0x7E819669",
    "NEO6_MUSIC": "0x7E8156A9",
    "NEURAL_SURROUND": "0x7E8133CC",
    "CINE_DSP_SPEC": "0x7E819F60",
    "CINE_DSP_SFX": "0x7E815FA0",
    "CINE_DSP_ADV": "0x7E81DF20",
    "CINE_DSP_CONCERT": "0x7E818778",
    "CINE_DSP_JAZZ": "0x7E8137C8",
    "CINE_DSP_MUSICVID": "0x7E81CF30",
    "CINE_DSP_SPORTS": "0x7E811FE0",
    "MUSIC_ENHANCER_HI_ON": "0x7E811BE4",
    "MUSIC_ENHANCER_HI_OFF": "0x7E819B64",
    "PRESET_MEM_A": "0x1EE10EF1",
    "PRESET_MEM_B": "0x1EE14EB1",
    "PRESET_MEM_C": "0x1EE12ED1",
    "PRESET_CALL_A": "0x1EE18E71",
    "PRESET_CALL_B": "0x1EE1CE31",
    "PRESET_CALL_C": "0x1EE1AE51",
    "MEM_SAVE_U1": "0x1EE16E91",
    "MEM_SAVE_U2": "0x1EE11EE1",
    "MEM_SAVE_U3": "0x1EE15EA1",
    "MEM_LOAD_U1": "0x1EE1EE11",
    "MEM_LOAD_U2": "0x1EE19E61",
    "MEM_LOAD_U3": "0x1EE1DE21",
    "DEMO_ON": "0x1EE1D629",
    "DEMO_OFF": "0x1EE136C9",
}
