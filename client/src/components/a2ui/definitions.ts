import { z } from 'zod'

import type { CatalogDefinitions } from '@copilotkit/a2ui-renderer'

export const HOME_TUTOR_CATALOG_ID = 'home-tutor'
export const TUTOR_SURFACE_ID = 'tutor-panel'

export const homeTutorDefinitions = {
  TutorText: {
    description: '一段辅导讲解文字，用于向学生解释知识点或步骤。',
    props: z.object({
      text: z.string().describe('讲解正文'),
    }),
  },
  ActionChip: {
    description: '可点击的辅导操作按钮，如「详细讲讲」「给个提示」。',
    props: z.object({
      actionId: z.string().describe('操作标识，如 explain_more'),
      label: z.string().describe('按钮文案'),
    }),
  },
  AnswerCompare: {
    description: '并排展示学生答案与参考答案。',
    props: z.object({
      student: z.string().describe('学生答案'),
      reference: z.string().describe('参考答案'),
    }),
  },
  ProcessStep: {
    description: '解题过程中的一个步骤卡片。',
    props: z.object({
      title: z.string().optional().describe('步骤标题'),
      text: z.string().describe('步骤说明'),
      expanded: z.boolean().optional().describe('是否默认展开'),
    }),
  },
  HintLadder: {
    description: '由浅入深的提示列表。',
    props: z.object({
      items: z.array(z.string()).describe('提示条目，由浅到深'),
    }),
  },
  KeyFrameThumb: {
    description: '关键帧缩略图，用于展示板书或过程截图。',
    props: z.object({
      frameId: z.string().optional().describe('帧标识'),
      imageUrl: z.string().optional().describe('图片 URL'),
      label: z.string().optional().describe('展示标签'),
    }),
  },
} satisfies CatalogDefinitions
