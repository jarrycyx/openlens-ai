from datasets import load_dataset

# oh_sampled_ds = load_dataset("SWE-Gym/OpenHands-Sampled-Trajectories", cache_dir='data/')
# med_agent_gym_ds = load_dataset("MedAgentGym/SampledTrajs", cache_dir='data/')
oh_sampled_ds = load_dataset("data/SWE-Gym___open_hands-sampled-trajectories", cache_dir='data/')
# med_agent_gym_ds = load_dataset("data/MedAgentGym___sampled_trajs", cache_dir='data/')

print(oh_sampled_ds["train"][0])
# print(med_agent_gym_ds["train"][0])