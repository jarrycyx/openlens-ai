#数据集下载
from modelscope.msdatasets import MsDataset
ds =  MsDataset.load('common-pile/pubmed', subset_name='default', split='train', cache_dir='data/pubmed')
#您可按需配置 subset_name、split，参照“快速使用”示例代码


# modelscope download --dataset common-pile/pubmed --cache_dir data/pubmed