# Librerias ---------------------------------------------------------------
# Cargamos librerías
library(pacman)
p_load(tidyverse, dtplyr, geosphere, janitor, raster, rgdal,data.table,ggplot2,sf,leaflet,leaflet.extras,htmlwidgets,webshot,htmltools,ggspatial,rosm,cowplot)
options(scipen = 999) # Evitar notacion cientifica

# Directorio --------------------------------------------------------------
# Cargamos el directorio
directorio<-read.csv("/Users/javiroman/RGV Soluciones Dropbox/Javier Román Bautista/Contenido Marketing/Directorio/directorio.csv",fileEncoding = 'UTF-8-BOM')
directorio<-as.data.table(directorio)
for(i in 1:nrow(directorio)){
  assign(paste0(directorio[i,"variable"]),as.character(directorio[i,"valor"]))
}

# Oferta. La cargamos y preparamos. También las actividades.
denue_2021 <- denue_2021 <- load(denue_2021_ligera)
actividades <- read_csv(actividades)
# Las siguientes dos lineas es para verificar si se introdujeron actividades, subramas, ramas, subsectores o sectores.
nchar(actividades %>% pull(clave) %>% max())
nchar(actividades %>% pull(clave) %>% min())
# Con lo siguiente obtenemos la produccion de las actividades que nos interesan en la ubicación geográfica que queremos analizar.
scians <- actividades[,"clave"]
scians <- unlist(scians)
ent <- c(9) # Clave de la CDMX
denue_2021_2 <- denue_2021 %>% 
  filter(cve_ent==ent) %>%
  # filter(cve_mun==mun) %>%
  # mutate(codigo_sector=substr(codigo_act,start = 1,stop = 2)) %>%  filter(codigo_sector%in%scians) %>% # Si queremos sectores
  # filter(codigo_subsector%in%scians) %>% # Si queremos subsectores
  # filter(codigo_rama%in%scians) %>% # Si queremos ramas
  # filter(codigo_subrama%in%scians) %>% # Si queremos subramas
  filter(codigo_act%in%scians) %>% # Si queremos clases
  st_as_sf(coords=c("longitud","latitud"),
           crs=4326)
# Graficamos prueba
plot(denue_2021_2,max.plot=1)

# Cargamos los shapes de los estados
entidades <- st_read(entidades) %>% clean_names()
entidades <- st_make_valid(entidades) 
entidades <- st_transform(entidades, 4326)
entidades <- entidades %>% mutate(cve_edo = as.numeric(cve_edo))
cdmx <- entidades %>% filter(cve_edo==9)
# Graficamos prueba
plot(cdmx,max.plot=1)

# Cargamos los shapes de los municipios
municipios <- st_read(municipios) %>% clean_names()
municipios <- st_make_valid(municipios) 
municipios <- st_transform(municipios, 4326)
municipios <- municipios %>% mutate(cve_ent = as.numeric(cve_ent))
cdmx2 <- municipios %>% filter(cve_ent==9)
# Graficamos prueba
plot(cdmx2,max.plot=1)

# Hacemos el mapa

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

esri_ocean <- paste0('https://services.arcgisonline.com/arcgis/rest/services/',
                     'Ocean/World_Ocean_Base/MapServer/tile/${z}/${y}/${x}.jpeg')
canvas_gris <- paste0('https://services.arcgisonline.com/arcgis/rest/services/',
                      'Canvas/World_Light_Gray_Base/MapServer/tile/${z}/${y}/${x}.jpeg')

denue_2021_2 <- denue_2021_2 %>% mutate(indicador = ifelse(per_ocu=="6 a 10 personas","6-10",
                                                           ifelse(per_ocu=="0 a 5 personas","1-5","11 o más")))

break_tacos <- c("11 o más","6-10","1-5")

mapa <- ggplot(data = denue_2021_2) +
  annotation_map_tile(type = canvas_gris,
                      zoomin = 0) +
  geom_sf(data = cdmx,
          color = "black",
          fill = NA) +
  geom_sf(aes(color = indicador),
          size=.2) +
  theme_minimal() +
  scale_color_manual(breaks = break_tacos,
                    values=c("#746A58","#9F9480","#C2BBAE")) +
  annotation_scale(bar_cols = c("black", "white"),
                   pad_x = unit(0.25, "cm"),
                   pad_y = unit(0.25, "cm")) +
  annotation_north_arrow(location = "topright",
                         height = unit(1, "cm"),
                         width = unit(1, "cm"),) +
  theme(axis.text = element_blank(),
        axis.ticks = element_blank()) +
  labs(color = "Personas ocupadas en\ntaquerías y torterías\nde la CDMX") +
  guides(color = guide_legend(override.aes = list(size = 2))) +
  theme(legend.justification=c(0,1), 
        legend.position=c(1.05,.3),
        legend.key.height = unit(.4, 'cm'), 
        legend.key.width = unit(.4, 'cm'),
        legend.title = element_text(colour="#9F9480", 
                                    size=8,
                                    face="bold"),
        legend.text = element_text(colour="black", 
                                   size=7),
        legend.background = element_rect(fill="transparent",
                                         size=0.5, linetype="solid")) +
  geom_sf(data = cdmx2,
          color = "black",
          size=.1,
          fill = NA)

mapa <- ggdraw(align_legend(mapa))

mapa

ggsave(
  mapa,
  file="mapa_tacosytortas.png",
  path = mapas,
  width = 1800,
  height = 1200,
  units = "px",
  dpi = 300,
  bg ="transparent",
)

resumen <- denue_2021_2 %>% group_by(indicador) %>% summarise(total = n())
etiquetas <- cdmx2 %>% st_drop_geometry() %>% dplyr::select(c("nom_mun"))
