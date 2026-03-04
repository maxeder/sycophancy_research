library(jsonlite)
library(tidyverse)

# Load Data

# no system prompt data 5 turn
# raw_data <- fromJSON("../data_old/judge_results_multiturn_v2301.json")

# no system prompt data 8 turn with reasoning judge
# raw_data <- fromJSON("../judge_output/reas_unprompted_judge_results_multiturn.json")

# no system prompt data 8 turn with non-reasoning judge 
# raw_data <- fromJSON("../judge_output/nonreas_unprompted_judge_results_multiturn.json")


# syc_judge_results_multiturn

# raw_data <- fromJSON("../judge_output/syc_judge_results_multiturn.json")

# non-sycophantic system prompt
# raw_data <- fromJSON("../judge_output/sys_prompt_short_judge_results_multiturn.json")


raw_data <- fromJSON("../judge_output/gemini_new_unprompted_judge_results_multiturn.json")





colors <- c("Pro" = "#0072B2", "Con" = "#D55E00")

# Flatten and Clean
# Extract relevant metadata and unnest the classified response scores
df_scores <- as_tibble(raw_data) %>%
  select(case_id, topic_key, user_stance, classified_response) %>%
  unnest(classified_response) %>% 
  select(case_id, topic_key, user_stance, turn, mean_score)

# df_scores %>%  
#   filter(turn == 1) %>% 
#   summary()


# Calculate average agreement score per turn across all topics/cases
df_trend <- df_scores %>%
  group_by(turn, user_stance) %>%
  summarise(
    avg_agreement = mean(mean_score, na.rm = TRUE),
    se_agreement = sd(mean_score, na.rm = TRUE) / sqrt(n()),
    .groups = "drop"
  )


# Mean of conditions & delta between conditions
stance_means <- df_scores %>%
  group_by(user_stance) %>%
  summarize(avg_score = mean(mean_score, na.rm = TRUE))

delta_value <- stance_means$avg_score[stance_means$user_stance == "Pro"] - 
  stance_means$avg_score[stance_means$user_stance == "Con"]

print(stance_means)
print(delta_value)


# Plot
ggplot(df_scores, aes(x = turn, y = mean_score, color = user_stance, fill = user_stance)) +
  
  # Raw Data Points
  geom_jitter(width = 0.05, height = 0.05, alpha = 0.3, size = 1.5) +
  
  # Error Ribbon
  # with standard error
  stat_summary(geom = "ribbon", fun.data = mean_se, alpha = 0.2, color = NA) +
  # with 95% Confidence Interval
  # stat_summary(geom = "ribbon", fun.data = mean_cl_normal, alpha = 0.2, color = NA) +
  
  # Trend Line
  # connect mean score of each turn
  stat_summary(fun = mean, geom = "line", linewidth = 1.2) +
  
  # Mean Points
  # dot for the average at each turn
  stat_summary(fun = mean, geom = "point", size = 3, shape = 21, color = "white", stroke = 1) +
  
  scale_color_manual(values = colors) +
  scale_fill_manual(values = colors) +
  
  # Styling and Labels
  scale_y_continuous(limits = c(-2, 2), breaks = seq(-2, 2, 1)) +
  scale_x_continuous(breaks = unique(df_scores$turn)) +
  labs(
#     title = "Model Agreement with Debate Topic over Turns",
    title = "Evolution of Model Stance over 8 Turns",
    # subtitle = "Raw response scores (dots) vs. Average trend (line)",
    subtitle = "Model responses to synthetic pro/con user inputs across 5 debate topics (T=0; 2 replications).\nPoints show mean stance scores calculated from 3 sentences per response. Ribbon shows Standard Error.",
    color = "User Stance", 
    fill = "User Stance",
    x = "Conversation Turn",
    y = "Classification Score (Alignment with Topic)"
  ) +
  theme_minimal() +
  theme(legend.position = "bottom")