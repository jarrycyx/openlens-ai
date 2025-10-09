from modelscope.msdatasets import MsDataset


ds = MsDataset.load('swift/github-code', split='train', languages=["Python"], cache_dir='data/github_code_modelscope', trust_remote_code=True)

# datasets version: https://github.com/modelscope/modelscope/issues/1498