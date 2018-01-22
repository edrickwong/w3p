
# coding: utf-8

# In[2]:


import numpy as np
import pandas as pd
np.random.seed(1)

# In[5]:


full_labels = pd.read_csv('images.csv')

# In[6]:


full_labels.head()

# In[13]:


grouped = full_labels.groupby('filename')
grouped.apply(lambda x: len(x)).value_counts()
gb = full_labels.groupby('filename')
grouped_list = [gb.get_group(x) for x in gb.groups]

# In[15]:


TRAINING_PERCENTAGE = 0.7

train_index = np.random.choice(len(grouped_list), size=int(TRAINING_PERCENTAGE*len(grouped_list)), replace=False)
test_index = np.setdiff1d(range(len(grouped_list)), train_index)

# In[18]:


train = pd.concat([grouped_list[i] for i in train_index])
test = pd.concat([grouped_list[i] for i in test_index])
len(train), len(test)

# In[19]:


train.to_csv('train_labels.csv', index=None)
test.to_csv('test_labels.csv', index=None)
