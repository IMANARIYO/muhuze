import fs from "node:fs";
import path from "node:path";

const API_URL =
  "https://gis-server.statistics.gov.rw/server/rest/services/Hosted/Village_Boundary_2022/FeatureServer/3/query";

const OUTPUT_FILE = path.resolve(
  "src/data/location/rwanda.ts"
);

const PAGE_SIZE = 2000;

const fields = [
  "province",
  "province_id",
  "district",
  "district_id",
  "sector",
  "sector_id",
  "cell",
  "cell_id",
  "village",
  "village_id",
].join(",");

/**
 * Convert a name into a safe ID.
 *
 * Example:
 * "City of Kigali"
 * -> "city-of-kigali"
 */
function slugify(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/**
 * Preserve the IDs already used by MUHUZE
 * for the five provinces.
 */
const provinceIdMap = {
  "City of Kigali": "kigali-city",
  "Northern Province": "northern-province",
  "Southern Province": "southern-province",
  "Eastern Province": "eastern-province",
  "Western Province": "western-province",
};

/**
 * Fetch one page from NISR.
 */
async function fetchPage(offset) {
  const params = new URLSearchParams({
    where: "1=1",
    outFields: fields,
    returnGeometry: "false",
    resultOffset: String(offset),
    resultRecordCount: String(PAGE_SIZE),
    orderByFields: "village_id ASC",
    f: "json",
  });

  const response = await fetch(
    `${API_URL}?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(
      `NISR request failed: ${response.status} ${response.statusText}`
    );
  }

  const data = await response.json();

  if (data.error) {
    throw new Error(
      `NISR API error: ${JSON.stringify(data.error)}`
    );
  }

  return data;
}

/**
 * Fetch all NISR records.
 */
async function fetchAllRecords() {
  const records = [];

  let offset = 0;

  while (true) {
    console.log(
      `Downloading NISR records ${offset} - ${
        offset + PAGE_SIZE
      }...`
    );

    const data = await fetchPage(offset);

    const features = data.features || [];

    for (const feature of features) {
      if (feature.attributes) {
        records.push(feature.attributes);
      }
    }

    if (
      features.length < PAGE_SIZE &&
      !data.exceededTransferLimit
    ) {
      break;
    }

    offset += PAGE_SIZE;
  }

  return records;
}

/**
 * Build nested structure:
 *
 * Province
 *   District
 *     Sector
 *       Cell
 *         Village
 */
function buildHierarchy(records) {
  const provinces = new Map();

  for (const record of records) {
    const provinceName =
      record.province?.trim();

    const districtName =
      record.district?.trim();

    const sectorName =
      record.sector?.trim();

    const cellName =
      record.cell?.trim();

    const villageName =
      record.village?.trim();

    if (
      !provinceName ||
      !districtName ||
      !sectorName ||
      !cellName ||
      !villageName
    ) {
      continue;
    }

    const provinceCode =
      String(record.province_id);

    const districtCode =
      String(record.district_id);

    const sectorCode =
      String(record.sector_id);

    const cellCode =
      String(record.cell_id);

    const villageCode =
      String(record.village_id);

    /*
     * Province
     */
    if (!provinces.has(provinceCode)) {
      provinces.set(provinceCode, {
        id:
          provinceIdMap[provinceName] ||
          slugify(provinceName),

        code: provinceCode,

        name: provinceName,

        districts: [],
      });
    }

    const province =
      provinces.get(provinceCode);

    /*
     * District
     */
    let district =
      province.districts.find(
        (item) =>
          item.code === districtCode
      );

    if (!district) {
      district = {
        id: slugify(districtName),

        code: districtCode,

        name: districtName,

        sectors: [],
      };

      province.districts.push(
        district
      );
    }

    /*
     * Sector
     */
    let sector =
      district.sectors.find(
        (item) =>
          item.code === sectorCode
      );

    if (!sector) {
      sector = {
        id: slugify(sectorName),

        code: sectorCode,

        name: sectorName,

        cells: [],
      };

      district.sectors.push(
        sector
      );
    }

    /*
     * Cell
     */
    let cell =
      sector.cells.find(
        (item) =>
          item.code === cellCode
      );

    if (!cell) {
      cell = {
        id: slugify(cellName),

        code: cellCode,

        name: cellName,

        villages: [],
      };

      sector.cells.push(cell);
    }

    /*
     * Village
     */
    const villageExists =
      cell.villages.some(
        (item) =>
          item.code === villageCode
      );

    if (!villageExists) {
      cell.villages.push({
        id: slugify(villageName),

        code: villageCode,

        name: villageName,
      });
    }
  }

  return Array.from(
    provinces.values()
  );
}

/**
 * Generate TypeScript source.
 */
function generateTypeScript(
  provinces
) {
  const json =
    JSON.stringify(
      provinces,
      null,
      2
    );

  return `/**
 * Rwanda Administrative Location Data
 *
 * Source:
 * National Institute of Statistics of Rwanda (NISR)
 *
 * Hierarchy:
 * Province
 *   -> District
 *      -> Sector
 *         -> Cell
 *            -> Village
 *
 * Generated automatically from
 * NISR Village Boundary 2022 Open Data.
 */

export interface RwandaVillage {
  id: string;
  code: string;
  name: string;
}

export interface RwandaCell {
  id: string;
  code: string;
  name: string;
  villages: RwandaVillage[];
}

export interface RwandaSector {
  id: string;
  code: string;
  name: string;
  cells: RwandaCell[];
}

export interface RwandaDistrict {
  id: string;
  code: string;
  name: string;
  sectors: RwandaSector[];
}

export interface RwandaProvince {
  id: string;
  code: string;
  name: string;
  districts: RwandaDistrict[];
}

export const rwandaProvinces: RwandaProvince[] =
${json};

/**
 * Find province by MUHUZE ID.
 */
export function getProvinceById(
  provinceId: string
): RwandaProvince | undefined {
  return rwandaProvinces.find(
    (province) =>
      province.id === provinceId ||
      province.code === provinceId
  );
}

/**
 * Get districts belonging to a province.
 */
export function getDistrictsByProvinceId(
  provinceId: string
): RwandaDistrict[] {
  return (
    getProvinceById(provinceId)
      ?.districts ?? []
  );
}

/**
 * Find district.
 */
export function getDistrictById(
  provinceId: string,
  districtId: string
): RwandaDistrict | undefined {
  return getDistrictsByProvinceId(
    provinceId
  ).find(
    (district) =>
      district.id === districtId ||
      district.code === districtId
  );
}

/**
 * Get sectors belonging to a district.
 */
export function getSectorsByDistrictId(
  provinceId: string,
  districtId: string
): RwandaSector[] {
  return (
    getDistrictById(
      provinceId,
      districtId
    )?.sectors ?? []
  );
}

/**
 * Find sector.
 */
export function getSectorById(
  provinceId: string,
  districtId: string,
  sectorId: string
): RwandaSector | undefined {
  return getSectorsByDistrictId(
    provinceId,
    districtId
  ).find(
    (sector) =>
      sector.id === sectorId ||
      sector.code === sectorId
  );
}

/**
 * Get cells belonging to a sector.
 */
export function getCellsBySectorId(
  provinceId: string,
  districtId: string,
  sectorId: string
): RwandaCell[] {
  return (
    getSectorById(
      provinceId,
      districtId,
      sectorId
    )?.cells ?? []
  );
}

/**
 * Find cell.
 */
export function getCellById(
  provinceId: string,
  districtId: string,
  sectorId: string,
  cellId: string
): RwandaCell | undefined {
  return getCellsBySectorId(
    provinceId,
    districtId,
    sectorId
  ).find(
    (cell) =>
      cell.id === cellId ||
      cell.code === cellId
  );
}

/**
 * Get villages belonging to a cell.
 */
export function getVillagesByCellId(
  provinceId: string,
  districtId: string,
  sectorId: string,
  cellId: string
): RwandaVillage[] {
  return (
    getCellById(
      provinceId,
      districtId,
      sectorId,
      cellId
    )?.villages ?? []
  );
}
`;
}

/**
 * Main
 */
async function main() {
  console.log(
    "🇷🇼 MUHUZE Rwanda Location Generator"
  );

  console.log(
    "Source: NISR Village Boundary 2022"
  );

  const records =
    await fetchAllRecords();

  console.log(
    `Downloaded ${records.length} village records.`
  );

  if (records.length === 0) {
    throw new Error(
      "No NISR records were returned."
    );
  }

  const provinces =
    buildHierarchy(records);

  const output =
    generateTypeScript(provinces);

  fs.mkdirSync(
    path.dirname(OUTPUT_FILE),
    {
      recursive: true,
    }
  );

  fs.writeFileSync(
    OUTPUT_FILE,
    output,
    "utf8"
  );

  console.log("");
  console.log(
    `✅ Generated: ${OUTPUT_FILE}`
  );

  console.log(
    `✅ Provinces: ${provinces.length}`
  );

  const districts =
    provinces.flatMap(
      (province) =>
        province.districts
    );

  const sectors =
    districts.flatMap(
      (district) =>
        district.sectors
    );

  const cells =
    sectors.flatMap(
      (sector) =>
        sector.cells
    );

  const villages =
    cells.flatMap(
      (cell) =>
        cell.villages
    );

  console.log(
    `✅ Districts: ${districts.length}`
  );

  console.log(
    `✅ Sectors: ${sectors.length}`
  );

  console.log(
    `✅ Cells: ${cells.length}`
  );

  console.log(
    `✅ Villages: ${villages.length}`
  );
}

main().catch((error) => {
  console.error("");
  console.error(
    "❌ Rwanda location generation failed."
  );

  console.error(error);

  process.exit(1);
});