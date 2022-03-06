# Librerias ---------------------------------------------------------------
# Cargamos librerías
library(pacman)
p_load(tidyverse, dtplyr, geosphere, janitor, raster, rgdal,data.table,ggplot2,sf,leaflet,leaflet.extras,htmlwidgets,scales)
options(scipen = 999) # Evitar notacion cientifica


# Directorio --------------------------------------------------------------
# Cargamos el directorio
directorio<-read.csv("/Users/javiroman/RGV Soluciones Dropbox/Javier Román Bautista/Contenido Marketing/Directorio/directorio.csv",fileEncoding = 'UTF-8-BOM')
directorio<-as.data.table(directorio)
for(i in 1:nrow(directorio)){
  assign(paste0(directorio[i,"variable"]),as.character(directorio[i,"valor"]))
}

# Mapa Seguros ------------------------------------------------------------
# Cargamos los shapes de los estados de Mexico
entidades <- st_read(entidades) %>% clean_names()
entidades <- st_make_valid(entidades) 
entidades <- st_transform(entidades, 4326)
entidades <- entidades %>% mutate(cve_edo = as.numeric(cve_edo))
# Cargamos la informacion del indice de siniestralidad
indice_siniestros <- read_csv(indice_sin) %>% clean_names() %>% 
  dplyr::select(-c("entidad"))
entidades_siniestros <- left_join(entidades,indice_siniestros,by=c("cve_edo"="clave"))
# Hacemos las etiquetas y pop up del mapa
pal <- colorBin("viridis", domain = entidades_siniestros$indice_de_siniestralidad, bins=6)
x <- label_percent(accuracy=0.01, scale=100.00)
label_entidades <- lapply(str_c("<b>Entidad: </b>",entidades_siniestros$entidad,"<br>",
                                "<b>Índice Siniestralidad: </b>",x(entidades_siniestros$indice_de_siniestralidad)),htmltools::HTML)
popup_entidades <- str_c("<b>Entidad: </b>",entidades_siniestros$entidad,"<br>",
                         "<b>Índice Siniestralidad: </b>",x(entidades_siniestros$indice_de_siniestralidad),"<br>",
                         "<b>Prima emitida millones de pesos: </b> $",prettyNum(entidades_siniestros$prima_emitida_millones_de_pesos,
                                                                    big.mark = ","),"<br>",
                         "<b>Siniestros ocurridos millones de pesos: </b> $",prettyNum(entidades_siniestros$siniestros_ocurridos_millones_de_pesos,
                                                                                       big.mark = ","))

# Hacemos el mapa
mapa <- leaflet() %>% addProviderTiles(provider = providers$CartoDB.DarkMatter) %>%
  setView( lng = -101.63116287350847
           , lat = 21.87342856577024
           , zoom = 4.5) %>%
  addPolygons(data = entidades_siniestros,
              fillColor = pal(entidades_siniestros$indice_de_siniestralidad),
              label = label_entidades,
              popup = popup_entidades,
              weight = 1,
              color="white",
              fillOpacity = 1) %>% 
  addLegend(title = "Índice de siniestralidad en México",
            position = "bottomright",
            labels = c("-20% - 0%","0% - 20%","20% - 40%","40% - 60%","60% - 80%","80% - 100%","100% - 120%","120% - 140%","140% - 160%"),
            colors = c("#440154","#472d7b","#3b528b","#2c728e","#21918c","#28ae80","#5ec962","#addc30","#fde725"),
            opacity = 1) %>%
  addScaleBar(position = "bottomleft")

saveWidget(mapa,paste0(mapas,"/mapa_siniestros_mexico.html"))


