# Librerias ---------------------------------------------------------------
# Cargamos librerías
library(pacman)
p_load(tidyverse, dtplyr, geosphere, janitor, raster, rgdal,data.table,ggplot2,sf,leaflet,leaflet.extras,htmlwidgets,scales,stringr)
options(scipen = 999) # Evitar notacion cientifica


# Directorio --------------------------------------------------------------
# Cargamos el directorio
directorio<-read.csv("/Users/javiroman/RGV Soluciones Dropbox/Javier Román Bautista/Contenido Marketing/Directorio/directorio.csv",fileEncoding = 'UTF-8-BOM')
directorio<-as.data.table(directorio)
for(i in 1:nrow(directorio)){
  assign(paste0(directorio[i,"variable"]),as.character(directorio[i,"valor"]))
}


# Datos denue noviembre 2021 ------------------------------------------------
load(denue_2021_ligera)
denue_2021 <- as.data.frame(denue)
rm(denue)
# Obtenemos el resumen de la distribucion por sector económico de la denue
denue_2021_resumen <- denue_2021 %>% dplyr::select(id,nom_estab,codigo_act) %>% 
  mutate(subsector = substr(codigo_act, 1, 2)) %>% 
  group_by(subsector) %>% 
  summarise(total_unidades = n()) %>% 
  ungroup()
denue_2021_resumen <- denue_2021_resumen %>% mutate(total_unidades_rel = total_unidades/sum(denue_2021_resumen$total_unidades)*100)
resumen <- denue_2019_resumen %>% rename(total_unidades_rel2019 = total_unidades_rel) %>% 
  left_join(denue_2021_resumen,by=c("subsector"))
# Guardamos los resultados
write_csv(resumen,paste0(data,"/tabla_resumen_denues.csv"))
