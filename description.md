## how to use this tool

upload any dataset you want (via url or direct file upload (drag-and-drop is supported)), and then set the parameters of the parallel coordinates plot. we currently support `csv`, `xls[x]`, and `dat` (for fixed with). as far as what gets renderd, you have a few options:

+ **included features**: these are the features which will appear as separate vertical bars in the parallel coordinates plot above. for each vertical bar, you can click and drag to select regions of these features and highlight the records which fall within that region for that feature.
+ **target feature**: the lines that are drawn (representing records in your dataset) are colored based on some target feature.
+ **color scale**: categorical features will have a choice of several colorscales emphasizing a distinct number of well-differentiated colors, while numeric features will receive a standard gradient colorscale. in addition to the built-in `plotly` colorscales, we are also leveraging the `colorlover` colorscales.
