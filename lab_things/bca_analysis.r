# Boilerplate
# Based off of Thermo's Pierce kit that recommends a quadratic fit
library(tidyverse)
library(mgcv)
library(ggplot2)
library(dplyr)

# Load in dictionaries
df = read.csv("bsa.csv")
key = read.csv("bca_key.csv")
standards = read.csv("bca_standards.csv")

df <- df %>% pivot_longer(!Row, names_to="Col", values_to="abs")
df$Well <- paste(df$Row, df$Col, sep="")
df <- merge(df, key)

# Subtract out blank
blank <- df %>% filter(Contains == "standard_SE")
df$abs <- df$abs - first(blank$abs)

# Extract standards from dataframe and model curve
df_standards <- df[grepl("standard", df$Contains, ignore.case = TRUE), ]
df <- df[!grepl("standard", df$Contains, ignore.case = TRUE), ]
names(df_standards)[names(df_standards) == 'Contains'] <- 'standard'
df_standards <- merge(df_standards, standards)

df_standards$amnt2 <- df_standards$amnt^2

quadraticModel <- lm(abs ~ amnt + amnt2, data=df_standards)
predicted_standards <- data.frame(abs_pred = predict(quadraticModel, df_standards), amnt=df_standards$amnt)

# Build and apply regression
coefs <- coef(quadraticModel)
a <- coefs["amnt2"]  # Quadratic term
b <- coefs["amnt"]   # Linear term
c_eq <- coefs["(Intercept)"]
df$c <- c_eq - df$abs

solve_quadratic <- function(c){
  discriminant <- b^2 - 4*a*c
  if (discriminant < 0){
    0
  } else {
    sol1 <- (-b + sqrt(discriminant)) / (2*a)
    sol2 <- (-b - sqrt(discriminant)) / (2*a)
    valid_solutions <- c(sol1, sol2)
    valid_solutions <- valid_solutions[valid_solutions >= 0]
    valid_solutions <- valid_solutions[valid_solutions <= 2500]
    first(valid_solutions)    
  }
}

df$amnt <- as.numeric(df$c %>% map(solve_quadratic))

ggplot() + geom_point(df_standards, mapping = aes(x=amnt, y=abs), color="grey") + theme_bw() +
  geom_smooth(data=predicted_standards, mapping = aes(x=amnt, y=abs_pred), color="black") +
  geom_point(df, mapping = aes(x=amnt, y=abs), color="purple")

df <- df[c("Contains", "Soluble", "Replicate", "amnt")]
