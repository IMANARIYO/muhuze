import { useEffect, useState } from "react";

import {
  rwandaProvinces,
  getDistrictsByProvinceId,
  getSectorsByDistrictId,
  getCellsBySectorId,
  getVillagesByCellId,
  type RwandaDistrict,
  type RwandaSector,
  type RwandaCell,
  type RwandaVillage,
} from "../../data/location/rwanda";

interface Props {
  provinceId?: string;
  districtId?: string;
  sectorId?: string;
  cellId?: string;
  villageId?: string;

  onChange?: (location: {
    provinceId: string;
    provinceName: string;

    districtId: string;
    districtName: string;

    sectorId: string;
    sectorName: string;

    cellId: string;
    cellName: string;

    villageId: string;
    villageName: string;
  }) => void;
}

export default function RwandaLocationSelector({
  provinceId = "",
  districtId = "",
  sectorId = "",
  cellId = "",
  villageId = "",
  onChange,
}: Props) {
  const [selectedProvince, setSelectedProvince] =
    useState(provinceId);

  const [selectedDistrict, setSelectedDistrict] =
    useState(districtId);

  const [selectedSector, setSelectedSector] =
    useState(sectorId);

  const [selectedCell, setSelectedCell] =
    useState(cellId);

  const [selectedVillage, setSelectedVillage] =
    useState(villageId);

  const [districts, setDistricts] =
    useState<RwandaDistrict[]>([]);

  const [sectors, setSectors] =
    useState<RwandaSector[]>([]);

  const [cells, setCells] =
    useState<RwandaCell[]>([]);

  const [villages, setVillages] =
    useState<RwandaVillage[]>([]);

  /*
   * Province → District
   */
  useEffect(() => {
    if (!selectedProvince) {
      setDistricts([]);
      return;
    }

    setDistricts(
      getDistrictsByProvinceId(
        selectedProvince
      )
    );
  }, [selectedProvince]);

  /*
   * District → Sector
   */
  useEffect(() => {
    if (
      !selectedProvince ||
      !selectedDistrict
    ) {
      setSectors([]);
      return;
    }

    setSectors(
      getSectorsByDistrictId(
        selectedProvince,
        selectedDistrict
      )
    );
  }, [
    selectedProvince,
    selectedDistrict,
  ]);

  /*
   * Sector → Cell
   */
  useEffect(() => {
    if (
      !selectedProvince ||
      !selectedDistrict ||
      !selectedSector
    ) {
      setCells([]);
      return;
    }

    setCells(
      getCellsBySectorId(
        selectedProvince,
        selectedDistrict,
        selectedSector
      )
    );
  }, [
    selectedProvince,
    selectedDistrict,
    selectedSector,
  ]);

  /*
   * Cell → Village
   */
  useEffect(() => {
    if (
      !selectedProvince ||
      !selectedDistrict ||
      !selectedSector ||
      !selectedCell
    ) {
      setVillages([]);
      return;
    }

    setVillages(
      getVillagesByCellId(
        selectedProvince,
        selectedDistrict,
        selectedSector,
        selectedCell
      )
    );
  }, [
    selectedProvince,
    selectedDistrict,
    selectedSector,
    selectedCell,
  ]);

  /*
   * Send complete location to parent
   */
  useEffect(() => {
    if (
      !selectedProvince ||
      !selectedDistrict ||
      !selectedSector ||
      !selectedCell ||
      !selectedVillage
    ) {
      return;
    }

    const province =
      rwandaProvinces.find(
        (item) =>
          item.id === selectedProvince
      );

    const district =
      districts.find(
        (item) =>
          item.id === selectedDistrict
      );

    const sector =
      sectors.find(
        (item) =>
          item.id === selectedSector
      );

    const cell =
      cells.find(
        (item) =>
          item.id === selectedCell
      );

    const village =
      villages.find(
        (item) =>
          item.id === selectedVillage
      );

    if (
      !province ||
      !district ||
      !sector ||
      !cell ||
      !village
    ) {
      return;
    }

    onChange?.({
      provinceId: province.id,
      provinceName: province.name,

      districtId: district.id,
      districtName: district.name,

      sectorId: sector.id,
      sectorName: sector.name,

      cellId: cell.id,
      cellName: cell.name,

      villageId: village.id,
      villageName: village.name,
    });
  }, [
    selectedProvince,
    selectedDistrict,
    selectedSector,
    selectedCell,
    selectedVillage,
    districts,
    sectors,
    cells,
    villages,
    onChange,
  ]);

  function handleProvinceChange(
    value: string
  ) {
    setSelectedProvince(value);

    setSelectedDistrict("");
    setSelectedSector("");
    setSelectedCell("");
    setSelectedVillage("");

    setSectors([]);
    setCells([]);
    setVillages([]);
  }

  function handleDistrictChange(
    value: string
  ) {
    setSelectedDistrict(value);

    setSelectedSector("");
    setSelectedCell("");
    setSelectedVillage("");

    setCells([]);
    setVillages([]);
  }

  function handleSectorChange(
    value: string
  ) {
    setSelectedSector(value);

    setSelectedCell("");
    setSelectedVillage("");

    setVillages([]);
  }

  function handleCellChange(
    value: string
  ) {
    setSelectedCell(value);
    setSelectedVillage("");
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

      {/* Country */}

      <div>
        <label className="block mb-2 font-medium">
          Country
        </label>

        <select
          value="rwanda"
          disabled
          className="
            w-full
            rounded-xl
            border
            border-gray-300
            bg-gray-100
            px-4
            py-3
          "
        >
          <option value="rwanda">
            Rwanda
          </option>
        </select>
      </div>

      {/* Province */}

      <div>
        <label className="block mb-2 font-medium">
          Province / City
        </label>

        <select
          value={selectedProvince}
          onChange={(event) =>
            handleProvinceChange(
              event.target.value
            )
          }
          className="
            w-full
            rounded-xl
            border
            border-gray-300
            bg-white
            px-4
            py-3
          "
        >
          <option value="">
            Select Province / City
          </option>

          {rwandaProvinces.map(
            (province) => (
              <option
                key={province.id}
                value={province.id}
              >
                {province.name}
              </option>
            )
          )}
        </select>
      </div>

      {/* District */}

      <div>
        <label className="block mb-2 font-medium">
          District
        </label>

        <select
          value={selectedDistrict}
          disabled={!selectedProvince}
          onChange={(event) =>
            handleDistrictChange(
              event.target.value
            )
          }
          className="
            w-full
            rounded-xl
            border
            border-gray-300
            bg-white
            px-4
            py-3
            disabled:bg-gray-100
          "
        >
          <option value="">
            Select District
          </option>

          {districts.map(
            (district) => (
              <option
                key={district.id}
                value={district.id}
              >
                {district.name}
              </option>
            )
          )}
        </select>
      </div>

      {/* Sector */}

      <div>
        <label className="block mb-2 font-medium">
          Sector
        </label>

        <select
          value={selectedSector}
          disabled={!selectedDistrict}
          onChange={(event) =>
            handleSectorChange(
              event.target.value
            )
          }
          className="
            w-full
            rounded-xl
            border
            border-gray-300
            bg-white
            px-4
            py-3
            disabled:bg-gray-100
          "
        >
          <option value="">
            Select Sector
          </option>

          {sectors.map(
            (sector) => (
              <option
                key={sector.id}
                value={sector.id}
              >
                {sector.name}
              </option>
            )
          )}
        </select>
      </div>

      {/* Cell */}

      <div>
        <label className="block mb-2 font-medium">
          Cell
        </label>

        <select
          value={selectedCell}
          disabled={!selectedSector}
          onChange={(event) =>
            handleCellChange(
              event.target.value
            )
          }
          className="
            w-full
            rounded-xl
            border
            border-gray-300
            bg-white
            px-4
            py-3
            disabled:bg-gray-100
          "
        >
          <option value="">
            Select Cell
          </option>

          {cells.map(
            (cell) => (
              <option
                key={cell.id}
                value={cell.id}
              >
                {cell.name}
              </option>
            )
          )}
        </select>
      </div>

      {/* Village */}

      <div>
        <label className="block mb-2 font-medium">
          Village
        </label>

        <select
          value={selectedVillage}
          disabled={!selectedCell}
          onChange={(event) =>
            setSelectedVillage(
              event.target.value
            )
          }
          className="
            w-full
            rounded-xl
            border
            border-gray-300
            bg-white
            px-4
            py-3
            disabled:bg-gray-100
          "
        >
          <option value="">
            Select Village
          </option>

          {villages.map(
            (village) => (
              <option
                key={village.id}
                value={village.id}
              >
                {village.name}
              </option>
            )
          )}
        </select>
      </div>

    </div>
  );
}