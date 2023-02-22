seaborn color: 
'Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap', 'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy', 'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r', 'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary', 'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r', 'cividis', 'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'crest', 'crest_r', 'cubehelix', 'cubehelix_r', 'flag', 'flag_r', 'flare', 'flare_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r', 'gist_ncar', 'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gnuplot', 'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r', 'hsv', 'hsv_r', 'icefire', 'icefire_r', 'inferno', 'inferno_r', 'jet', 'jet_r', 'magma', 'magma_r', 'mako', 'mako_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r', 'rainbow', 'rainbow_r', 'rocket', 'rocket_r', 'seismic', 'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r', 'tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r', 'turbo', 'turbo_r', 'twilight', 'twilight_r', 'twilight_shifted', 'twilight_shifted_r', 'viridis', 'viridis_r', 'vlag', 'vlag_r', 'winter', 'winter_r'



[
    {
        "name": ".check",
        "type": "e",
        "short": "",
        "long": "--check",
        "default": null,
        "section": "General options",
        "description": "Check parameters in cmd-line.",
        "vignettes": "Check if the parameter definitions are correct. "
    },
    {
        "name": "repeat",
        "type": "b",
        "short": "-r",
        "long": "--repeat",
        "default": 1,
        "section":"Draw plot",
        "description": "A boolean parameter to show if the results are repeat or not",
        "vignettes": "Enable the use of repeatition. This option is only availiable when \\parameter{execDir} is not None. When using this option, the results from \\crace should have more than 1 repetitions with the same setting except the parameter seed. When unusing this option, the results from \\crace should have only one race."
    },
    {
        "name": "elitist",
        "type": "b",
        "short": "",
        "long": "--elitist",
        "default": 0,
        "section":"Draw plot",
        "description": "Enable\/disable the analysis on only the elitist configuration for each repetition.",
        "vignettes": "Enable\/disable the analysis on only the elitist configuration for each repetition. The default value is 0 (False), which means we select the top5 elite configuartions or all configurations. When it is set as 1 (True), only the elitist configuration in each repetition will be selected."
    },
    {
        "name": "allConfigurations",
        "type": "b",
        "short": "",
        "long": "--all-configurations",
        "default": 0,
        "section": "Draw plot",
        "description": "Enable\/disable the analysis on all configurations for each repetition.",
        "vignettes":"Enable\/disable the analysis on all configurations for each repetition. The default value is 0 (False), which means we select the top5 elite configuartions or the elitist. When it is set as 1 (True), all configurations in each repetition will be selected."
    }
]