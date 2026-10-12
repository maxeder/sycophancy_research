# Model opinion for positive vs. negative users: single-turn, multi-turn, simulated user, real users.
# Input (conversations joined with judge scores on case_id), from benchmark/:
#   syco export runs/thesis_multi_turn runs/thesis_user_study --combined thesis
#   syco export runs/<simulated_user run(s)> --combined simulated_user
# Run from benchmark/analysis_r_v2/.

library(tidyverse)

turns <- bind_rows(read_csv("../results/thesis_turns.csv", show_col_types = FALSE),
                   read_csv("../results/simulated_user_turns.csv", show_col_types = FALSE)) %>%
  filter(role == "assistant", turn >= 1, !is.na(mean_score)) %>%  # turn 0 = greeting / stance before user input
  mutate(stance = case_when(
    approach %in% c("multi_turn", "simulated_user") ~ if_else(user_stance == "pro", "Positive", "Negative"),
    meta_pre_opinion > 4 ~ "Positive",  # real users: pre-study Likert 1-7, 4 = neutral (dropped)
    meta_pre_opinion < 4 ~ "Negative")) %>%
  filter(!is.na(stance))

# One model-opinion value per conversation: turn 1 for single-turn, mean over turns otherwise
opinion <- bind_rows(
  `Single-turn` = filter(turns, approach == "multi_turn", turn == 1),
  `Multi-turn`  = filter(turns, approach == "multi_turn"),
  `Simulated user` = filter(turns, approach == "simulated_user"),
  `Real users`  = filter(turns, approach == "real_world"),
  .id = "source") %>%
  group_by(source, condition, stance, case_id) %>%
  summarise(opinion = mean(mean_score), .groups = "drop") %>%
  mutate(source    = factor(source, c("Single-turn", "Multi-turn", "Simulated user", "Real users")),
         condition = factor(condition, c("unprompted", "sycophantic", "contrarian"),
                            c("Unprompted", "Sycophantic", "Contrarian")),
         stance    = factor(stance, c("Positive", "Negative")))

count(opinion, source, condition, stance)

opinion_plot <- ggplot(opinion, aes(source, opinion, colour = stance, shape = stance)) +
  geom_hline(yintercept = 0, linetype = "dashed", colour = "grey70") +
  stat_summary(fun.data = mean_cl_normal, position = position_dodge(width = 0.2), size = 0.8, linewidth = 0.7) +
  facet_wrap(~ condition) +
  scale_x_discrete(labels = scales::label_wrap(10)) +  # four sources per facet: wrap "Simulated user" etc.
  scale_colour_manual(values = c(Positive = "#2a78d6", Negative = "#eb6834")) +
  coord_cartesian(ylim = c(-2, 2)) +
  labs(x = NULL, y = "Model opinion (judge score, -2 to +2)", colour = "User opinion", shape = "User opinion") +
  theme_minimal(base_size = 15) +
  theme(legend.position = "top", panel.grid.major.x = element_blank(), panel.grid.minor = element_blank())
opinion_plot

dir.create("plots", showWarnings = FALSE)
ggsave("plots/opinion_by_source.pdf", opinion_plot, width = 12, height = 4.5)
ggsave("plots/opinion_by_source.png", opinion_plot, width = 12, height = 4.5, dpi = 300, bg = "white")
