import { createCatalog } from '@copilotkit/a2ui-renderer'

import { HOME_TUTOR_CATALOG_ID, homeTutorDefinitions } from './definitions'
import { homeTutorRenderers } from './renderers'

export const homeTutorCatalog = createCatalog(homeTutorDefinitions, homeTutorRenderers, {
  catalogId: HOME_TUTOR_CATALOG_ID,
  includeBasicCatalog: false,
})
