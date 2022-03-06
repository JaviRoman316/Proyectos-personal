# Librerias ---------------------------------------------------------------
# Cargamos librerías
library(pacman)
p_load(tidyverse, dtplyr, geosphere, janitor, raster, rgdal,data.table,ggplot2,sf,leaflet,leaflet.extras,htmlwidgets,webshot,htmltools,ggspatial,rosm,cowplot,BAMMtools)
options(scipen = 999) # Evitar notacion cientifica

# Directorio --------------------------------------------------------------
# Cargamos el directorio
directorio<-read.csv("/Users/javiroman/RGV Soluciones Dropbox/Javier Román Bautista/Contenido Marketing/Directorio/directorio.csv",fileEncoding = 'UTF-8-BOM')
directorio<-as.data.table(directorio)
for(i in 1:nrow(directorio)){
  assign(paste0(directorio[i,"variable"]),as.character(directorio[i,"valor"]))
}

# Cargamos los shapes de los estados
entidades <- st_read(entidades) %>% clean_names()
entidades <- st_make_valid(entidades)
entidades <- st_transform(entidades, 4326)
entidades <- entidades %>% mutate(cve_edo = as.numeric(cve_edo))
# Graficamos prueba
plot(entidades,max.plot=1)

# Obtenemos el TDPA por entidad
datos_viales <- read_csv(datos_viales) %>% clean_names()
datos_viales <- datos_viales %>%
  left_join(entidades %>% st_drop_geometry() %>% dplyr::select("entidad","cve_edo"),by=c("estado"="entidad"))
datos_viales <- datos_viales %>% mutate(cve_edo = ifelse(!is.na(cve_edo),cve_edo,ifelse(estado=="CDMX",9,
                                                     ifelse(estado=="Coahuila",5,
                                                                            ifelse(estado=="Michoacán",16,
                                                                                   ifelse(estado=="Querétaro",22,
                                                                                          ifelse(estado=="San Luis Potosí",24,30)))))))

# Juntamos TDPA por entidad al shape de los estados que tendrán tambien
entidades <- entidades %>% dplyr::select(-c(area,perimeter,cov,cov_id,capital))
datos_viales <- datos_viales %>% dplyr::select(-c(estado))
carreteras <- entidades %>% left_join(datos_viales,by=c("cve_edo"))

# Obtenemos los kilometros de las carreteras estatales y federales
carreteras_estatales <- read_csv(carreteras_estatales) %>% dplyr::select(c("cve_ent","long_kilometros"))
carreteras_federales <- read_csv(carreteras_federales) %>% dplyr::select(c("cve_ent","km"))
carreteras <- carreteras %>% left_join(carreteras_estatales,by=c("cve_edo"="cve_ent")) %>%
  left_join(carreteras_federales,by=c("cve_edo"="cve_ent"))

# Hacemos el mapa
carreteras <- carreteras %>% mutate(indicador = tdpa_entidad/(km + long_kilometros)) %>% mutate(indicador = round(indicador,digits = 0))
intervalos <- getJenksBreaks(carreteras$indicador,6)
intervalos
carreteras <- carreteras %>%
  mutate(nueva=ifelse(indicador>intervalos[5],"3,072",ifelse(indicador>intervalos[4],"164 - 229",ifelse(indicador>intervalos[3],"103 - 163",
                                                                                                           ifelse(indicador>intervalos[2],"46 - 102","45 o menos")))))
carreteras$nueva <- as.character(carreteras$nueva)

# La siguiente funcion es para centrar la leyenda del mapa
align_legend <- function(p, hjust = 0.5)
{
  # extract legend
  g <- cowplot::plot_to_gtable(p)
  grobs <- g$grobs
  legend_index <- which(sapply(grobs, function(x) x$name) == "guide-box")
  legend <- grobs[[legend_index]]

  # extract guides table
  guides_index <- which(sapply(legend$grobs, function(x) x$name) == "layout")

  # there can be multiple guides within one legend box
  for (gi in guides_index) {
    guides <- legend$grobs[[gi]]

    # add extra column for spacing
    # guides$width[5] is the extra spacing from the end of the legend text
    # to the end of the legend title. If we instead distribute it by `hjust:(1-hjust)` on
    # both sides, we get an aligned legend
    spacing <- guides$width[5]
    guides <- gtable::gtable_add_cols(guides, hjust*spacing, 1)
    guides$widths[6] <- (1-hjust)*spacing
    title_index <- guides$layout$name == "title"
    guides$layout$l[title_index] <- 2

    # reconstruct guides and write back
    legend$grobs[[gi]] <- guides
  }

  # reconstruct legend and write back
  g$grobs[[legend_index]] <- legend
  g
}

canvas_gris <- paste0('https://services.arcgisonline.com/arcgis/rest/services/',
                      'Canvas/World_Light_Gray_Base/MapServer/tile/${z}/${y}/${x}.jpeg')

mapa <- ggplot(data = carreteras) +
  annotation_map_tile(type = canvas_gris,
                      zoomin = 0) +
  geom_sf(aes(fill = nueva),
          color = "black",
          size=.1) +
  theme_minimal() +
  scale_fill_manual(breaks = c("3,072", "164 - 229","103 - 163","46 - 102","45 o menos"),
                    values=c("#C30C3E","#204A6F","#3477B2","#A0C4E3","#EFF5FA"),
  ) +
  annotation_scale(bar_cols = c("black", "white"),
                   pad_x = unit(0.25, "cm"),
                   pad_y = unit(0.25, "cm"),
                   text_col = "black") +
  annotation_north_arrow(location = "topright",
                         height = unit(0.75, "cm"),
                         width = unit(0.75, "cm"),
                         style = north_arrow_orienteering(fill = c("white", "black"),
                                                          text_col = "black")) +
  theme(axis.text = element_blank(),
        axis.ticks = element_blank()) +
  labs(fill = "Tránsito Diario Promedio Anual\npor km de carretera") +
  theme(legend.justification=c(0,1),
        legend.position=c(.02,.45),
        legend.key.height = unit(.4, 'cm'),
        legend.key.width = unit(.4, 'cm'),
        legend.title = element_text(colour="#3477B2",
                                    size=7,
                                    face="bold"),
        legend.text = element_text(colour="black",
                                   size=6),
        legend.background = element_rect(fill="transparent",
                                         size=0.5, linetype="solid",
                                         colour ="gray"),
  )

mapa <- ggdraw(align_legend(mapa))

mapa

ggsave(
  mapa,
  file="mapa_carreteras.png",
  path = mapas,
  width = 1560,
  height = 1170,
  units = "px",
  dpi = 300,
  bg ="transparent",
)

