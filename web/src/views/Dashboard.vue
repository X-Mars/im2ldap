<template>
  <div class="dashboard">

    <!-- 数据卡片行 -->
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in cards" :key="card.title">
        <el-card class="data-card" :class="card.type">
          <div class="card-content">
            <div class="card-icon">
              <img v-if="card.imgIcon" :src="card.imgIcon" class="card-img-icon" />
              <el-icon v-else><component :is="card.icon" /></el-icon>
            </div>
            <div class="card-info">
              <div class="title">{{ card.title }}</div>
              <div class="value">{{ card.value }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表行 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <h3>用户数趋势</h3>
              <el-radio-group v-model="timeRange" size="small">
                <el-radio-button value="week">本周</el-radio-button>
                <el-radio-button value="month">本月</el-radio-button>
                <el-radio-button value="year">全年</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <base-chart :option="userTrendChartOption" height="360px" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <sync-status-widget />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { getNoteStats, getActiveUsers } from '@/api'
import { getUserTrend } from '@/api/sync'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import {
  Document,
  FolderOpened,
  User,
  SwitchButton
} from '@element-plus/icons-vue'
import type { EChartsOption } from 'echarts'
import BaseChart from '@/components/BaseChart.vue'
import SyncStatusWidget from '@/components/SyncStatusWidget.vue'
import wecomImg from '@/assets/wecom.png'
import feishuImg from '@/assets/feishu.png'
import dingtalkImg from '@/assets/dingtalk.png'
import ldapImg from '@/assets/ldap.png'

const router = useRouter()
const userStore = useUserStore()
const user = computed(() => userStore.user)

// 处理退出登录
const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const timeRange = ref('week')

const cards = ref([
  {
    title: '企业微信用户',
    value: 0,
    type: 'primary',
    icon: 'Document',
    imgIcon: wecomImg,
    trend: 0
  },
  {
    title: '飞书用户',
    value: 0,
    type: 'success',
    icon: 'FolderOpened',
    imgIcon: feishuImg,
    trend: 0
  },
  {
    title: '钉钉用户',
    value: 0,
    type: 'warning',
    icon: 'User',
    imgIcon: dingtalkImg,
    trend: 0
  },
  {
    title: 'OpenLDAP用户',
    value: 0,
    type: 'info',
    icon: 'User',
    imgIcon: ldapImg,
    trend: 0
  }
])

const fetchStats = async () => {
  try {
    const userTrendRes = await getUserTrend(timeRange.value);
    
    if (userTrendRes.data.current_stats) {
      cards.value[0].value = userTrendRes.data.current_stats.wecom_users;
      cards.value[1].value = userTrendRes.data.current_stats.feishu_users;
      cards.value[2].value = userTrendRes.data.current_stats.dingtalk_users;
      cards.value[3].value = userTrendRes.data.current_stats.ldap_users;
    }

    userTrendChartOption.value = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderColor: '#eee',
        borderWidth: 1,
        textStyle: {
          color: '#666'
        }
      },
      legend: {
        data: ['企业微信', '飞书', '钉钉', 'OpenLDAP'],
        right: '10%',
        top: '0%'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: userTrendRes.data.dates,
        axisLine: {
          lineStyle: {
            color: '#ddd'
          }
        }
      },
      yAxis: {
        type: 'value',
        axisLine: {
          show: false
        },
        splitLine: {
          lineStyle: {
            color: '#eee'
          }
        }
      },
      series: [
        {
          name: '企业微信',
          type: 'line',
          smooth: true,
          data: userTrendRes.data.wecom_users,
          lineStyle: {
            width: 3,
            color: '#409EFF'
          },
          symbol: 'circle',
          symbolSize: 6
        },
        {
          name: '飞书',
          type: 'line',
          smooth: true,
          data: userTrendRes.data.feishu_users,
          lineStyle: {
            width: 3,
            color: '#67C23A'
          },
          symbol: 'circle',
          symbolSize: 6
        },
        {
          name: '钉钉',
          type: 'line',
          smooth: true,
          data: userTrendRes.data.dingtalk_users,
          lineStyle: {
            width: 3,
            color: '#E6A23C'
          },
          symbol: 'circle',
          symbolSize: 6
        },
        {
          name: 'OpenLDAP',
          type: 'line',
          smooth: true,
          data: userTrendRes.data.ldap_users,
          lineStyle: {
            width: 3,
            color: '#909399'
          },
          symbol: 'circle',
          symbolSize: 6
        }
      ]
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

watch(timeRange, () => {
  fetchStats()
})

onMounted(async () => {
  await userStore.fetchUserInfo()
  fetchStats()
})

const userTrendChartOption = ref<EChartsOption>({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderColor: '#eee',
    borderWidth: 1,
    textStyle: {
      color: '#666'
    }
  },
  legend: {
    data: ['企业微信', '飞书', '钉钉', 'OpenLDAP'],
    right: '10%',
    top: '0%'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    axisLine: {
      lineStyle: {
        color: '#ddd'
      }
    }
  },
  yAxis: {
    type: 'value',
    axisLine: {
      show: false
    },
    splitLine: {
      lineStyle: {
        color: '#eee'
      }
    }
  },
  series: [
    {
      name: '企业微信',
      type: 'line',
      smooth: true,
      data: [150, 165, 158, 172, 168, 180, 185],
      lineStyle: {
        width: 3,
        color: '#409EFF'
      },
      symbol: 'circle',
      symbolSize: 6
    },
    {
      name: '飞书',
      type: 'line',
      smooth: true,
      data: [100, 110, 115, 112, 120, 122, 124],
      lineStyle: {
        width: 3,
        color: '#67C23A'
      },
      symbol: 'circle',
      symbolSize: 6
    },
    {
      name: '钉钉',
      type: 'line',
      smooth: true,
      data: [120, 132, 128, 140, 145, 150, 156],
      lineStyle: {
        width: 3,
        color: '#E6A23C'
      },
      symbol: 'circle',
      symbolSize: 6
    },
    {
      name: 'OpenLDAP',
      type: 'line',
      smooth: true,
      data: [200, 205, 210, 208, 215, 212, 220],
      lineStyle: {
        width: 3,
        color: '#909399'
      },
      symbol: 'circle',
      symbolSize: 6
    }
  ]
})

</script>

<style scoped>

.card-img-icon {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.dashboard {
  padding: 10px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 130px);
}

/* 数据卡片样式 */
.data-card {
  margin-bottom: 20px;
  border-radius: 15px;
  border: none;
  transition: transform 0.3s;
}

.data-card:hover {
  transform: translateY(-5px);
}

.card-content {
  display: flex;
  align-items: center;
  padding: 10px;
  justify-content: space-between;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.card-img-icon {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.primary .card-icon {
  background-color: rgba(64, 158, 255, 0.1);
  color: #409EFF;
}

.success .card-icon {
  background-color: rgba(103, 194, 58, 0.1);
  color: #67C23A;
}

.warning .card-icon {
  background-color: rgba(230, 162, 60, 0.1);
  color: #E6A23C;
}

.info .card-icon {
  background-color: rgba(144, 147, 153, 0.1);
  color: #909399;
}

.card-info {
  text-align: right;
}

.card-info .value {
  font-size: 24px;
  font-weight: bold;
  margin-top: 5px;
}

.card-info .title {
  font-size: 14px;
  color: #909399;
}

/* 图表卡片样式 */
.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  border-radius: 15px;
  border: none;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.chart-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

:deep(.el-radio-button__inner) {
  border-radius: 20px !important;
}

:deep(.el-button) {
  border-radius: 25px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-card__body) {
  padding: 20px;
}

/* 添加用户信息样式 */
.user-info {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 100;
}

.user-dropdown-link {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-right: 10px;
  font-size: 14px;
  color: #606266;
}

.avatar {
  background-color: #409EFF;
  color: #fff;
  font-weight: bold;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-dropdown-menu__item .el-icon) {
  margin-right: 4px;
}
</style> 