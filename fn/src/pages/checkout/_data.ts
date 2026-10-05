/** Rwanda's provinces and their districts. Sectors and cells are typed by the buyer. */
export const provinces: Record<string, string[]> = {
  'Kigali City': ['Gasabo', 'Kicukiro', 'Nyarugenge'],
  Northern: ['Burera', 'Gakenke', 'Gicumbi', 'Musanze', 'Rulindo'],
  Southern: ['Gisagara', 'Huye', 'Kamonyi', 'Muhanga', 'Nyamagabe', 'Nyanza', 'Nyaruguru', 'Ruhango'],
  Eastern: ['Bugesera', 'Gatsibo', 'Kayonza', 'Kirehe', 'Ngoma', 'Nyagatare', 'Rwamagana'],
  Western: ['Karongi', 'Ngororero', 'Nyabihu', 'Nyamasheke', 'Rubavu', 'Rusizi', 'Rutsiro'],
}

/** Rwandan mobile numbers: MTN (078, 079) and Airtel (072, 073), ten digits. */
export const phoneField = {
  type: 'tel',
  inputMode: 'numeric',
  pattern: '07[2389][0-9]{7}',
  maxLength: 10,
  placeholder: '078 / 072 …',
  title: 'Ten digits starting with 078, 079, 072 or 073',
} as const
