# Librerias ---------------------------------------------------------------
# Cargamos librerías
library(pacman)
p_load(tidyverse, dtplyr, geosphere, janitor, raster, rgdal,data.table,ggplot2,sf,leaflet,leaflet.extras,htmlwidgets,scales,networkD3,readxl,webshot,treemapify)
options(scipen = 999) # Evitar notacion cientifica


# Directorio --------------------------------------------------------------
# Cargamos el directorio
directorio<-read.csv("Directorio/directorio.csv",fileEncoding = 'UTF-8-BOM')
directorio<-as.data.table(directorio)
for(i in 1:nrow(directorio)){
  assign(paste0(directorio[i,"variable"]),as.character(directorio[i,"valor"]))
}

# Treemap ciberseguridad --------------------------------------------------
# Cargamos datos
ciberdelitos <- read_csv(treemap_seguridad) %>% clean_names()
treemap_seg <- ciberdelitos %>% 
  ggplot(aes(area=incidentes_reportados,
             fill=tipo,
             subgroup = tipo,
             label=subtipo)) +
  geom_treemap(color = "white") +
  geom_treemap_subgroup_border(size = 1, color="gray") +
  scale_fill_manual(values = c("#3477B2","#9D90A0","#253356","#364C81","#7F8FA9")) +
  geom_treemap_text(fontface = "italic",
                    colour = "white",
                    place = "centre",
                    grow = F,
                    reflow=T) +
  geom_treemap_subgroup_text(place = "bottom",
                             grow = T,
                             alpha = 0.5,
                             colour = "#FAFAFA",
                             min.size = 0) +
  theme(legend.position = "none")
ggsave(
  file="treemap_seg.png",
  plot = treemap_seg,
  path = graficas,
  width = 12,
  height = 10.20,
  units = "cm")
  
