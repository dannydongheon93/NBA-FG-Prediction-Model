library(car)
library(leaps)
library(dplyr)

setwd("~/UVA/Linear Models/Final Project")
#masterfile <- read.csv("timeingame_test.csv", header = TRUE, na.strings = "")
masterfile1 <- read.csv("NBA_2014_Final_combined_withFG_DefFGPerc_onlyshot.csv", header = TRUE, na.strings = "")
masterfile <- masterfile1

# get rid of overtime shots
masterfile <- masterfile[masterfile$PERIOD_x <= 4,]

# limit to shots only
masterfile <- masterfile[masterfile$shot_or_not == 1,]
masterfile$FGM <- as.numeric(levels(masterfile$FGM))[masterfile$FGM]
masterfile <- masterfile[masterfile$FGM <= 1,]

# get rid of bad TOUCH_TIME observations
masterfile$TOUCH_TIME <- as.numeric(levels(masterfile$TOUCH_TIME))[masterfile$TOUCH_TIME]
masterfile <- masterfile[masterfile$TOUCH_TIME >= 0 & masterfile$TOUCH_TIME <= 24,]

# get rid of weird observations without shot clock values
masterfile <- masterfile[masterfile$SHOT_CLOCK != "NA",]

# get rid of shots where there was no matching record in the shot log file
masterfile <- masterfile[masterfile$SHOT_DIST != "NA",]

# get rid of duplicate rows
masterfile <- masterfile[!duplicated(masterfile[,c("EVENTNUM","GAME_ID")]),]

# keep only the columns needed for model
columns_tokeep <- c("SCOREMARGIN","LOCATION","SHOT_NUMBER","SHOT_CLOCK","DRIBBLES","TOUCH_TIME","SHOT_DIST","CLOSE_DEF_DIST","PTS",
                    "FGperc","DefFGperc","position","time_sub","shot_or_not","EVENTNUM","GAME_ID",
                    "Time_left","PCTIMESTRING","PTS_TYPE","FGM","PLAYER1_TEAM_NICKNAME", "PLAYER1_NAME")
masterfile <- masterfile[,colnames(masterfile) %in% columns_tokeep]

# drop the one observation that is NA
masterfile <- masterfile[!is.na(masterfile$time_sub),]
summary(masterfile)

# fix shots for which the shotclock column is blank
x <- masterfile[masterfile$shot_or_not == 1,]

for(i in 1:nrow(x))
{ 
  if(x[i,]$PCTIMESTRING == 0)
  {
    index <- which(masterfile$GAME_ID == x[i,"GAME_ID"] & masterfile$EVENTNUM == x[i,"EVENTNUM"])
    masterfile[index,"SHOT_CLOCK"] <- 1
    #24-masterfile[index-1,"PCTIMESTRING"]
  }
}


# get rid of columns that aren't being used anymore
masterfile <- masterfile[,!colnames(masterfile) %in% c("EVENTNUM","PCTIMESTRING","shot_or_not","Time_left")]


# put scoring margin, time_sub, SHOT_NUMBER into factors
masterfile <- masterfile[masterfile$SCOREMARGIN != "NA",]
x <- masterfile$SCOREMARGIN
levels(x) <- c(levels(x), "0")
x[x == "TIE"] <- 0
x <- as.numeric(levels(x))[x]
masterfile$SCOREMARGIN <- x

masterfile$time_sub_copy <- masterfile$time_sub
masterfile$time_sub <- cut(masterfile$time_sub, br = seq(from = 0, to = 2880, by = 500))

masterfile$PTS_TYPE  <- as.factor(masterfile$PTS_TYPE)

# Convert factors to numeric variables
masterfile$SHOT_CLOCK <- as.numeric(levels(masterfile$SHOT_CLOCK))[masterfile$SHOT_CLOCK]

masterfile$DRIBBLES <- as.numeric(levels(masterfile$DRIBBLES))[masterfile$DRIBBLES]

masterfile$TOUCH_TIME <- as.numeric(levels(masterfile$TOUCH_TIME))[masterfile$TOUCH_TIME]

masterfile$SHOT_DIST <- as.numeric(levels(masterfile$SHOT_DIST))[masterfile$SHOT_DIST]

masterfile$CLOSE_DEF_DIST <- as.numeric(levels(masterfile$CLOSE_DEF_DIST))[masterfile$CLOSE_DEF_DIST]

masterfile$PTS <- as.numeric(levels(masterfile$PTS))[masterfile$PTS]

masterfile$FGM <- as.numeric(levels(masterfile$FGM))[masterfile$FGM]

masterfile$SHOT_NUMBER <- as.numeric(levels(masterfile$SHOT_NUMBER))[masterfile$SHOT_NUMBER]

summary(masterfile)


# create logistic model
thesample <- sample(1:nrow(masterfile),nrow(masterfile)*.8, replace = FALSE)
training <- masterfile[thesample,]
testing <- masterfile[-thesample,]
shot.glm <- glm(FGM~. -PTS -PLAYER1_TEAM_NICKNAME -PLAYER1_NAME -GAME_ID -time_sub_copy,data = training, family = "binomial")
summary(shot.glm)
vif(shot.glm)

# drop dribbles because of multicollinearity with touch time and DefFGperc (not significant)
shot.glm2 <- glm(FGM~. -PTS -DRIBBLES -PLAYER1_TEAM_NICKNAME -PLAYER1_NAME -GAME_ID -time_sub_copy -DefFGperc,data = training, family = "binomial")
summary(shot.glm2)
vif(shot.glm2)

# calculate expected points per shot
shot.glm2$xlevels[["PLAYER1_NAME"]] <- union(shot.glm2$xlevels[["PLAYER1_NAME"]],levels(testing$PLAYER1_NAME))
testing$expFGperc <- predict(shot.glm2, newdata = testing, type = "response")
testing$exppoints <- testing$expFGperc*as.numeric(levels(testing$PTS_TYPE))[testing$PTS_TYPE]


# calculate model accuracy
decision_threshold <- seq(from = 0.1, to = 1, by = 0.05)
for(i in 1:length(decision_threshold))
{
  accuracy <- nrow(testing[testing$FGM == round(testing$expFGperc+(0.5-decision_threshold[i])),])/nrow(testing)
  print(decision_threshold[i])
  print(accuracy)
}


# Plot expected pts per shot vs actual PPS by each team
testing$PLAYER1_TEAM_NICKNAME <- as.character(testing$PLAYER1_TEAM_NICKNAME)
z <- group_by(testing,PLAYER1_TEAM_NICKNAME)
z1 <- summarise(z, mean(exppoints))
z2 <- summarise(z, mean(PTS))
z <- cbind(z1,z2$`mean(PTS)`)
z <- as.data.frame(z)
colnames(z) <- c("Team","Exp Points","Actual Points")
plot(z$`Exp Points`,z$`Actual Points`)
cor(z$`Exp Points`,z$`Actual Points`) # r = 0.756


# Plot expected pts per shot vs actual PPS by each player
testing$PLAYER1_NAME <- as.character(testing$PLAYER1_NAME)
y <- group_by(testing,PLAYER1_NAME)
y1 <- summarise(y, mean(exppoints))
y2 <- summarise(y, mean(PTS))
y3 <- summarise(y, n())
y <- cbind(y1,y2$`mean(PTS)`,y3$`n()`)
y <- as.data.frame(y)
colnames(y) <- c("Player","Exp Points","Actual Points", "Total Shots")
y <- y[y$`Total Shots`>=100,]
plot(y$`Exp Points`,y$`Actual Points`)



# Plot Steph Curry
curry <- group_by(testing[testing$PLAYER1_NAME == "Stephen Curry",],GAME_ID)
curry1 <- summarise(curry, mean(exppoints))
curry2 <- summarise(curry, mean(PTS))
curry <- cbind(curry1,curry2$`mean(PTS)`)
curry <- as.data.frame(curry)
colnames(curry) <- c("GAME_ID","Exp Points","Actual Points")
plot(curry$`Exp Points`,curry$`Actual Points`)
cor(curry$`Exp Points`,curry$`Actual Points`)

# look at exp points by time_sub
testing$time_sub_copy <- cut(testing$time_sub_copy, br = seq(from = 0, to = 2880, by = 200))
t <- group_by(testing,time_sub_copy)
t1 <- summarise(t, mean(exppoints))
t <- as.data.frame(t1)
colnames(t) <- c("Time in Game","Exp Points")

# look at exp points by score margin
testing1 <- testing
testing1$SCOREMARGIN <- cut(testing1$SCOREMARGIN, br = seq(from = -60, to = 60, by = 10))
sm <- group_by(testing1,SCOREMARGIN)
sm1 <- summarise(sm, mean(exppoints))
sm <- as.data.frame(sm1)
colnames(sm) <- c("Score Margin","Exp Points")

# look at exp points by shot number
thetable <- table(testing$SHOT_NUMBER, testing$PLAYER1_NAME)
thetable <- thetable[15:30,]
thetable <- thetable[,colSums(thetable)>0]
volumeshooters <- colnames(thetable)
testing1 <- testing
testing1 <- testing1[testing1$PLAYER1_NAME %in% volumeshooters,]
shot <- group_by(testing1,SHOT_NUMBER)
shot1 <- summarise(shot, mean(exppoints))
shot <- as.data.frame(shot1)
colnames(shot) <- c("Shot Number","Exp Points")

# look at exp points by shot clock
testing1 <- testing
testing1$SHOT_CLOCK <- cut(testing1$SHOT_CLOCK, br = seq(from = -1, to = 24, by = 5))
clock <- group_by(testing1,SHOT_CLOCK)
clock1 <- summarise(clock, mean(exppoints))
clock <- as.data.frame(clock1)
colnames(clock) <- c("Shot Clock","Exp Points")

# look at exp points by score margin
testing1 <- testing
testing1$TOUCH_TIME <- cut(testing1$TOUCH_TIME, br = seq(from = -1, to = 26, by = 3))
touch <- group_by(testing1,TOUCH_TIME)
touch1 <- summarise(touch, mean(exppoints))
touch <- as.data.frame(touch1)
colnames(touch) <- c("Touch Time","Exp Points")


##########################################
#
# visualizations
#
##########################################

library(ggplot2)
library(iplots)

t1<-theme(                              
  plot.background = element_blank(), 
  panel.grid.major = element_blank(), 
  panel.grid.minor = element_blank(), 
  panel.border = element_blank(), 
  panel.background = element_blank(),
  axis.line = element_line(size=.4)
)

p1 <- ggplot(z, aes(x = z$`Exp Points`, y = z$`Actual Points`)) + geom_point(color="red") + geom_smooth(method = "lm", se = TRUE)+ labs(x="Expected Points Per Shot", y = "Actual Points Per Shot",title= "2014 Shots")  + theme_bw() + geom_text(x = 1.04, y = .92, label = "Teams", size = 30)
print(p1)
p1 <- ggplot(z, aes(x = z$`Exp Points`, y = z$`Actual Points`)) + geom_point(color="red") + geom_smooth(method = "lm", se = TRUE)+ labs(x="Expected Points Per Shot", y = "Actual Points Per Shot",title= "2014 Shots")  + theme_bw() + geom_text(aes(label=z$Team)) + geom_text(x = 1.04, y = .92, label = "Teams", size = 30)
print(p1)

p2 <- ggplot(y, aes(x = y$`Exp Points`, y = y$`Actual Points`)) + geom_point(color="blue") + geom_smooth(method = "lm", se = TRUE)+ labs(x="Expected Points Per Shot", y = "Actual Points Per Shot",title= "2014 Shots")  + theme_bw() + geom_text(x = 1.15, y = .7, label = "Players", size = 25)
print(p2)
data=subset(y, abs(y$`Exp Points`-y$`Actual Points`)>.15)
p2 <- ggplot(y, aes(x = y$`Exp Points`, y = y$`Actual Points`)) + geom_point(color="blue") + geom_smooth(method = "lm", se = TRUE)+ labs(x="Expected Points Per Shot", y = "Actual Points Per Shot",title= "2014 Shots")  + theme_bw()+ geom_text(data=subset(y, abs(y$`Exp Points`-y$`Actual Points`)>.15),aes(x = data$`Exp Points`, y = data$`Actual Points`,label=data$Player))+ geom_text(x = 1.15, y = .7, label = "Players", size = 25) 
print(p2)

p3 <- ggplot(t, aes(x = t$`Time in Game`, y = t$`Exp Points`, group = 1)) + geom_point(color="red")+ geom_smooth(method = "lm", se = TRUE)+ labs(x="Time in Game", y = "Expected Points Per Shot",title= "2014 Shots")  + theme_bw()
print(p3)

p4 <- ggplot(sm, aes(x = sm$`Score Margin`, y = sm$`Exp Points`, group = 1)) + geom_point(color="red")+ geom_smooth(method = "lm", se = TRUE)+ labs(x="Score Margin", y = "Expected Points Per Shot",title= "2014 Shots")  + theme_bw()
print(p4)

p5 <- ggplot(shot, aes(x = shot$`Shot Number`, y = shot$`Exp Points`, group = 1)) + geom_point(color="red")+ geom_smooth(method = "lm", se = TRUE)+ labs(x="Shot Number", y = "Expected Points Per Shot",title= "2014 Shots")  + theme_bw()
print(p5)

p6 <- ggplot(clock, aes(x = clock$`Shot Clock`, y = clock$`Exp Points`, group = 1)) + geom_point(color="red")+ geom_smooth(method = "lm", se = TRUE)+ labs(x="Shot Clock", y = "Expected Points Per Shot",title= "2014 Shots")  + theme_bw()
print(p6)

p7 <- ggplot(touch, aes(x = touch$`Touch Time`, y = touch$`Exp Points`, group = 1)) + geom_point(color="red")+ geom_smooth(method = "lm", se = TRUE)+ labs(x="Touch Time", y = "Expected Points Per Shot",title= "2014 Shots")  + theme_bw()
print(p7)
